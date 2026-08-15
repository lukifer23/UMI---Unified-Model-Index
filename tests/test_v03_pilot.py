from __future__ import annotations

import base64
import gzip
import json
import re
import socket
import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from analysis.claims import calibrate_release_claims
from analysis.gaps import pilot_gap_report
from analysis.pilot_sensitivity import analyze_pilot_sensitivity, family_budget_snapshot
from scripts.build_v03_pilot import main as build_v03_pilot
from scripts.freeze_v03_open_sources import _zip_content_sha256
from umi.adapters import (
    adapt_aa_facts,
    adapt_arena_json,
    adapt_deepswe_facts,
    adapt_epoch_arc_agi_2_zip,
    adapt_epoch_csv,
    adapt_epoch_external_benchmarks_zip,
    adapt_epoch_gpqa_zip,
    adapt_lab_release_facts,
)
from umi.bundle import build_acceptance_manifest, load_scoring_bundle, validate_scoring_bundle
from umi.certificate import build_comparison_certificate
from umi.config import ProjectConfig, load_project_config
from umi.derived_metrics import derive_efficiency_metric
from umi.fingerprints import dataset_fingerprint
from umi.loading import load_dataset, load_model_crosswalk, load_source_registry
from umi.readiness import readiness_failures
from umi.schemas import (
    AggregationStatistic,
    ArtifactCaptureType,
    CrosswalkStatus,
    IdentityAssurance,
    ModelCrosswalk,
    ModelCrosswalkEntry,
    OverlapEdge,
    OverlapRelation,
    RecordStatus,
    ScoringDisposition,
    SignalPolicy,
    SignalRole,
    UncertaintyKind,
)
from umi.scoring import score_bundle, score_dataset
from umi.source_policy import validate_crosswalk
from umi.validation import DataValidationError, validate_source_registry

ROOT = Path(__file__).parents[1]
SOURCES = ROOT / "data" / "sources" / "v0.3"
PILOT = ROOT / "data" / "pilots" / "v0.3" / "raw"


@pytest.fixture(scope="module")
def pilot_dataset():
    return load_dataset(PILOT)


@pytest.fixture(scope="module")
def pilot_config():
    return load_project_config(ROOT / "config")


@pytest.fixture(scope="module")
def crosswalk():
    return load_model_crosswalk(SOURCES / "crosswalk.yaml")


def test_frozen_registry_checksums_and_license_contract(pilot_dataset) -> None:
    registry = load_source_registry(ROOT / "data" / "sources" / "registry.yaml")
    report = validate_source_registry(
        registry, ROOT / "data" / "sources" / "registry.yaml", pilot_dataset
    )
    assert report.errors == ()
    pilot_snapshots = [item for item in registry.snapshots if "v0.3/" in item.artifact_path]
    assert len(pilot_snapshots) == 10
    assert all(item.license_id and item.attribution and item.adapter_id for item in pilot_snapshots)


def test_git_attributes_preserve_frozen_sources_and_normalize_generated_text() -> None:
    output = subprocess.run(
        [
            "git",
            "check-attr",
            "text",
            "eol",
            "--",
            "data/sources/v0.3/deepswe-reviewed-facts-2026-08-13.yaml",
            "data/pilots/v0.3/raw/benchmarks.yaml",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "data/sources/v0.3/deepswe-reviewed-facts-2026-08-13.yaml: text: unset" in output
    assert "data/pilots/v0.3/raw/benchmarks.yaml: text: set" in output
    assert "data/pilots/v0.3/raw/benchmarks.yaml: eol: lf" in output


def test_real_pilot_requires_a_valid_governance_bundle(
    pilot_dataset, pilot_config, crosswalk
) -> None:
    registry_path = ROOT / "data" / "sources" / "registry.yaml"
    registry = load_source_registry(registry_path)
    bundle = load_scoring_bundle(PILOT, ROOT / "config", registry_path, SOURCES / "crosswalk.yaml")
    assert bundle.dataset == pilot_dataset
    assert bundle.acceptance_manifest == build_acceptance_manifest(pilot_dataset, registry)
    assert bundle.acceptance_manifest.accepted_record_ids
    assert bundle.acceptance_manifest.excluded_diagnostic_record_ids

    scored = next(item for item in pilot_dataset.benchmarks if item.record_id.startswith("deepswe"))
    assert scored.capture_type == ArtifactCaptureType.REVIEWED_FACT_EXTRACT
    unbound = pilot_dataset.model_copy(
        update={
            "benchmarks": (
                scored.model_copy(update={"crosswalk_entry_id": None}),
                *tuple(item for item in pilot_dataset.benchmarks if item != scored),
            )
        }
    )
    assert any(
        "lacks an exact crosswalk binding" in error
        for error in validate_scoring_bundle(
            unbound, pilot_config, registry, registry_path, crosswalk
        )
    )

    uncaptured = pilot_dataset.model_copy(
        update={
            "benchmarks": (
                scored.model_copy(update={"capture_type": None}),
                *tuple(item for item in pilot_dataset.benchmarks if item != scored),
            )
        }
    )
    assert any(
        "lacks capture_type" in error
        for error in validate_scoring_bundle(
            uncaptured, pilot_config, registry, registry_path, crosswalk
        )
    )

    signals = tuple(
        item.model_copy(update={"disposition": ScoringDisposition.DIAGNOSTIC_ONLY})
        if item.id == "deepswe-v1.1"
        else item
        for item in pilot_config.overlap.signals
    )
    diagnostic_policy = pilot_config.model_copy(
        update={"overlap": pilot_config.overlap.model_copy(update={"signals": signals})}
    )
    assert any(
        "signal policy does not permit scoring" in error
        for error in validate_scoring_bundle(
            pilot_dataset, diagnostic_policy, registry, registry_path, crosswalk
        )
    )

    inferred_models = tuple(
        item.model_copy(update={"identity_assurance": IdentityAssurance.INFERRED})
        if item.id == scored.model_id
        else item
        for item in pilot_dataset.models
    )
    inferred_identity = pilot_dataset.model_copy(update={"models": inferred_models})
    assert any(
        "identity assurance is below label_exact" in error
        for error in validate_scoring_bundle(
            inferred_identity, pilot_config, registry, registry_path, crosswalk
        )
    )

    harness_efficiency = next(
        item
        for item in pilot_dataset.efficiency
        if item.model_id == scored.model_id and item.signal_id == "deepswe-v1.1-resources"
    )
    assert readiness_failures(
        harness_efficiency,
        next(item for item in pilot_dataset.models if item.id == scored.model_id),
    ) == ()
    efficiency = next(
        item
        for item in pilot_dataset.efficiency
        if item.model_id == scored.model_id
        and item.signal_id == "deepswe-v1.1-endpoint-resources"
    )
    assert "deployment identity is not verified for endpoint-sensitive evidence" in (
        readiness_failures(
            efficiency.model_copy(
                update={
                    "record_status": RecordStatus.READY,
                    "scoring_disposition": ScoringDisposition.SCORED,
                }
            ),
            next(item for item in pilot_dataset.models if item.id == scored.model_id),
        )
    )


def test_diagnostic_artifact_failure_blocks_strict_audit_but_not_scoring(
    pilot_dataset, pilot_config, crosswalk
) -> None:
    registry_path = ROOT / "data" / "sources" / "registry.yaml"
    registry = load_source_registry(registry_path)
    manifest = build_acceptance_manifest(pilot_dataset, registry)
    diagnostic_snapshot = next(
        item for item in registry.snapshots if item.id not in manifest.accepted_artifact_ids
    )
    corrupted = registry.model_copy(
        update={
            "snapshots": tuple(
                item.model_copy(update={"artifact_sha256": "0" * 64})
                if item.id == diagnostic_snapshot.id
                else item
                for item in registry.snapshots
            )
        }
    )

    assert validate_scoring_bundle(
        pilot_dataset, pilot_config, corrupted, registry_path, crosswalk
    ) == ()
    strict_report = validate_source_registry(
        corrupted, registry_path, pilot_dataset
    )
    assert any("checksum mismatch" in error for error in strict_report.errors)


def test_score_bundle_rejects_a_forged_acceptance_manifest() -> None:
    registry_path = ROOT / "data" / "sources" / "registry.yaml"
    bundle = load_scoring_bundle(PILOT, ROOT / "config", registry_path, SOURCES / "crosswalk.yaml")
    forged = bundle.acceptance_manifest.model_copy(
        update={"fingerprint": "0" * 64}
    )
    with pytest.raises(DataValidationError, match="acceptance manifest"):
        score_bundle(bundle.__class__(**{**bundle.__dict__, "acceptance_manifest": forged}))


def test_comparison_certificate_is_deterministic_and_source_bound() -> None:
    registry_path = ROOT / "data" / "sources" / "registry.yaml"
    bundle = load_scoring_bundle(
        PILOT, ROOT / "config", registry_path, SOURCES / "crosswalk.yaml"
    )
    models = ("claude-opus-5-max", "kimi-k3-max", "glm-5.2-max")
    first = build_comparison_certificate(bundle, models)
    second = build_comparison_certificate(bundle, tuple(reversed(models)))

    assert first == second
    assert first.status == "provisional_comparison"
    assert first.certificate_version == "umi-certificate-v0.1"
    assert len(first.result_fingerprint) == 64
    assert first.evidence_profile_id
    assert first.score_scale_id
    assert len(first.normalization_panel_ids) >= 2
    assert len(first.normalization_panel_ids) == len(first.applied_normalization)
    assert set(first.raw_contributions) == set(models)
    assert set(first.rank_robustness) == set(models)
    assert first.source_record_ids
    assert first.source_artifact_ids
    assert set(first.source_artifact_checksums) == set(first.source_artifact_ids)
    assert all(len(value) == 64 for value in first.source_artifact_checksums.values())
    assert any("same evidence-profile ID" == item for item in first.comparability_basis)

    forged = bundle.acceptance_manifest.model_copy(update={"fingerprint": "0" * 64})
    with pytest.raises(DataValidationError, match="acceptance manifest"):
        build_comparison_certificate(
            bundle.__class__(**{**bundle.__dict__, "acceptance_manifest": forged}), models
        )

    evidence_free = bundle.dataset.models[0].model_copy(
        update={"id": "evidence-free-model"}
    )
    abstaining_dataset = bundle.dataset.model_copy(
        update={"models": (*bundle.dataset.models, evidence_free)}
    )
    abstaining_bundle = bundle.__class__(
        **{
            **bundle.__dict__,
            "dataset": abstaining_dataset,
            "acceptance_manifest": build_acceptance_manifest(
                abstaining_dataset, bundle.source_registry
            ),
        }
    )
    abstention = build_comparison_certificate(
        abstaining_bundle, (bundle.dataset.models[0].id, evidence_free.id)
    )
    assert abstention.status == "insufficient_common_support"
    assert abstention.evidence_profile_id is None
    assert abstention.score_scale_id is None
    assert not abstention.component_scores
    assert abstention.abstention_reasons
    assert evidence_free.id in abstention.missing_evidence


def test_release_claim_non_comparisons_name_the_exact_failed_gate(pilot_dataset) -> None:
    reasons = {
        item["claim_record_id"]: item["reason"]
        for item in calibrate_release_claims(pilot_dataset)
    }
    assert reasons == {
        "openai-release-claim-deepswe-v1.1-gpt-5.6-sol-max-2026-07-09": "cohort_mismatch",
        "openai-release-claim-gdpval-aa-v2-gpt-5.6-sol-max-2026-07-09": "benchmark_mismatch",
        "openai-release-claim-gpqa-diamond-gpt-5.6-sol-max-2026-07-09": "cohort_mismatch",
        "openai-release-claim-terminalbench-2.1-gpt-5.6-sol-max-2026-07-09": "benchmark_mismatch",
    }


def test_crosswalk_exactness_and_rejected_aliases(pilot_dataset, crosswalk) -> None:
    report = validate_crosswalk(
        crosswalk,
        pilot_dataset,
        load_source_registry(ROOT / "data" / "sources" / "registry.yaml"),
    )
    assert report.valid
    rejected = {
        item.id: item.rejection_reason
        for item in crosswalk.entries
        if item.status == CrosswalkStatus.REJECTED
    }
    assert "fallback" in rejected["aa-fable-fallback-rejected"].lower()
    assert "effort" in rejected["arena-agent-sol-xhigh-rejected"].lower()
    assert "missing effort" in rejected["arena-text-fable-omitted-rejected"].lower()


def test_exact_crosswalk_rejects_missing_and_mismatched_effort() -> None:
    base = {
        "id": "bad",
        "source_id": "source",
        "source_artifact_id": "artifact",
        "upstream_revision": "revision",
        "source_model_id": "model",
        "canonical_model_id": "canonical",
        "match_evidence": "test",
        "status": "exact",
    }
    with pytest.raises(ValidationError, match="require source and canonical effort"):
        ModelCrosswalkEntry.model_validate(
            {**base, "source_effort": None, "canonical_effort": None}
        )
    with pytest.raises(ValidationError, match="effort must match"):
        ModelCrosswalkEntry.model_validate(
            {**base, "source_effort": "high", "canonical_effort": "max"}
        )


def test_crosswalk_detects_many_to_one_collision(crosswalk) -> None:
    exact = next(item for item in crosswalk.entries if item.status == CrosswalkStatus.EXACT)
    collision = exact.model_copy(update={"id": "collision", "source_model_id": "other"})
    report = validate_crosswalk(ModelCrosswalk(entries=(*crosswalk.entries, collision)))
    assert not report.valid
    assert any("multiple rows" in error for error in report.errors)


def test_crosswalk_detects_upstream_revision_change(pilot_dataset, crosswalk) -> None:
    entry = crosswalk.entries[0].model_copy(update={"upstream_revision": "changed"})
    changed = ModelCrosswalk(entries=(entry, *crosswalk.entries[1:]))
    report = validate_crosswalk(
        changed,
        pilot_dataset,
        load_source_registry(ROOT / "data" / "sources" / "registry.yaml"),
    )
    assert not report.valid
    assert any("upstream revision mismatch" in error for error in report.errors)


def test_adapters_are_offline_deterministic_and_role_safe(monkeypatch, crosswalk) -> None:
    def deny_network(*args, **kwargs):
        raise AssertionError("adapter attempted network access")

    monkeypatch.setattr(socket, "socket", deny_network)
    aa_first = adapt_aa_facts(SOURCES / "aa-reviewed-facts-2026-08-14.yaml", crosswalk)
    aa_second = adapt_aa_facts(SOURCES / "aa-reviewed-facts-2026-08-14.yaml", crosswalk)
    assert aa_first == aa_second
    assert len(aa_first.external_indexes) == 4
    assert len(aa_first.rejections) == 1
    assert all(
        item.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY
        for item in aa_first.external_indexes
    )
    deep = adapt_deepswe_facts(SOURCES / "deepswe-reviewed-facts-2026-08-13.yaml", crosswalk)
    assert len(deep.benchmarks) == 5
    assert all(item.uncertainty is not None for item in deep.benchmarks)
    assert all(
        item.uncertainty is not None
        and item.uncertainty.kind == UncertaintyKind.CONFIDENCE_INTERVAL
        and item.uncertainty.confidence_level == 0.95
        for item in deep.benchmarks
    )
    assert len(deep.efficiency) == 10
    harness_records = [
        item for item in deep.efficiency if item.signal_id == "deepswe-v1.1-resources"
    ]
    endpoint_records = [
        item
        for item in deep.efficiency
        if item.signal_id == "deepswe-v1.1-endpoint-resources"
    ]
    assert len(harness_records) == len(endpoint_records) == 5
    assert all(
        item.aggregation_statistic == AggregationStatistic.ARITHMETIC_MEAN
        and item.scoring_disposition == ScoringDisposition.SCORED
        and derive_efficiency_metric(item, "effective_input_tokens") is not None
        and derive_efficiency_metric(item, "effective_output_tokens") is not None
        and derive_efficiency_metric(item, "effective_agent_steps") is not None
        for item in harness_records
    )
    assert all(
        item.record_status == RecordStatus.DIAGNOSTIC_ONLY
        and item.mean_wall_seconds is not None
        and item.mean_cost_per_attempt is not None
        for item in endpoint_records
    )


def test_full_pilot_build_is_offline(monkeypatch) -> None:
    def deny_network(*args, **kwargs):
        raise AssertionError("pilot build attempted network access")

    monkeypatch.setattr(socket, "socket", deny_network)
    build_v03_pilot()
    processed = PILOT.parent / "processed"
    assert {
        "correlations.json",
        "model-specific-partial-estimates.json",
        "overlap.json",
        "pareto.json",
        "pilot-gap-report.json",
        "pilot-dashboard.json",
        "pilot-dashboard.html",
        "pilot-sensitivity.json",
    } <= {item.name for item in processed.iterdir()}
    dashboard = json.loads((processed / "pilot-dashboard.json").read_text(encoding="utf-8"))
    assert dashboard["surface"] == "dashboard"
    assert dashboard["snapshot"]["status"] == "partial"
    assert dashboard["snapshot"]["datasets"]["overview"] == [
        {
            "economics_coverage": 0.0,
            "efficiency_coverage": 0.045,
            "headline_ready": 0,
            "max_capability_coverage": 0.49375,
            "pilot_models": 5,
            "scored_capability_cells": 20,
            "total_capability_cells": 70,
        }
    ]
    assert all(
        item["headline"] == "Not eligible"
        for item in dashboard["snapshot"]["datasets"]["model_summary"]
    )
    assert len(dashboard["snapshot"]["datasets"]["benchmarks"]) == 20
    assert len(dashboard["snapshot"]["datasets"]["resources"]) == 5
    source_ids = {item["id"] for item in dashboard["sources"]}
    assert all(
        item["sourceId"] in source_ids
        for collection in ("cards", "charts", "tables")
        for item in dashboard["manifest"][collection]
    )
    html = (processed / "pilot-dashboard.html").read_text(encoding="utf-8")
    payload_match = re.search(
        r'<template\s+id=["\']data-analytics-portable-artifact-payload-source["\'][^>]*>'
        r"(.*?)</template>",
        html,
        re.DOTALL,
    )
    assert payload_match is not None
    embedded = json.loads(
        gzip.decompress(base64.b64decode(re.sub(r"\s+", "", payload_match.group(1))))
    )
    assert embedded["manifest"] == dashboard["manifest"]
    assert embedded["snapshot"] == dashboard["snapshot"]
    assert embedded["sources"] == dashboard["sources"]


def test_epoch_and_arena_adapter_dispositions(crosswalk) -> None:
    epoch = adapt_epoch_csv(
        SOURCES / "epoch-eci-benchmarks-2026-08-14.csv",
        crosswalk,
        source_id="epoch-eci",
        artifact_id="epoch-eci-matrix-2026-08-14",
    )
    assert epoch.external_indexes
    assert all(item.evaluation_date is None for item in epoch.external_indexes)
    assert all(item.model_release_date is not None for item in epoch.external_indexes)
    assert all(
        item.capture_type == ArtifactCaptureType.RAW_UPSTREAM_PAYLOAD
        for item in epoch.external_indexes
    )
    assert all(
        item.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY
        for item in epoch.external_indexes
    )
    arena = adapt_arena_json(
        SOURCES / "arena-agent-2026-08-14.json",
        crosswalk,
        source_id="arena-agent",
        artifact_id="arena-agent-2026-08-14",
        upstream_revision="08dd89df7a8aa9df2ead3799f6422af4ad2e97a7",
        subset="agent",
    )
    assert {item.model_id for item in arena.benchmarks} == {
        "claude-opus-5-max",
        "kimi-k3-max",
        "glm-5.2-max",
    }
    assert all(item.provider_snapshot_id is None for item in arena.benchmarks)
    assert all(item.evaluation_date is None for item in arena.benchmarks)
    assert all(item.leaderboard_publish_date is not None for item in arena.benchmarks)
    assert all(
        item.capture_type == ArtifactCaptureType.ARCHIVED_SOURCE_SNAPSHOT
        for item in arena.benchmarks
    )
    assert all(item.record_status == RecordStatus.DIAGNOSTIC_ONLY for item in arena.benchmarks)
    assert all(
        item.uncertainty is not None
        and item.uncertainty.kind == UncertaintyKind.CONFIDENCE_INTERVAL
        and item.uncertainty.confidence_level is None
        for item in arena.benchmarks
    )
    assert any("Fable" in item.source_row_id for item in arena.rejections)
    assert any("Sol" in item.source_row_id for item in arena.rejections)


def test_epoch_gpqa_is_exact_common_scored_capability(crosswalk) -> None:
    assert _zip_content_sha256(SOURCES / "epoch-benchmark-data-2026-08-14.zip") == (
        "2b818e5b5ad1fcdba9f04616d6f1c7f71714a3d045967dbf09a7e13bf557f009"
    )
    result = adapt_epoch_gpqa_zip(
        SOURCES / "epoch-benchmark-data-2026-08-14.zip",
        crosswalk,
        source_id="epoch-benchmarks",
        artifact_id="epoch-benchmark-data-2026-08-14",
    )
    assert len(result.benchmarks) == 4
    assert {item.source_row_id for item in result.rejections} == {"claude-fable-5_max"}
    assert {item.model_id for item in result.benchmarks} == {
        "claude-opus-5-max",
        "gpt-5.6-sol-max",
        "kimi-k3-max",
        "glm-5.2-max",
    }
    assert all(item.signal_id == "gpqa-diamond" for item in result.benchmarks)
    assert all(item.provider_snapshot_id is None for item in result.benchmarks)
    assert all(
        item.uncertainty is not None
        and item.uncertainty.kind == UncertaintyKind.STANDARD_ERROR
        and item.number_of_trials is None
        for item in result.benchmarks
    )


def test_epoch_external_benchmarks_preserve_source_date_and_reject_fallback(
    crosswalk,
) -> None:
    result = adapt_epoch_external_benchmarks_zip(
        SOURCES / "epoch-benchmark-data-2026-08-14.zip",
        crosswalk,
        source_id="epoch-benchmarks",
        artifact_id="epoch-benchmark-data-2026-08-14",
    )
    assert len(result.benchmarks) == 8
    assert {item.benchmark_id for item in result.benchmarks} == {"scicode", "critpt"}
    assert all(item.evaluation_date is None for item in result.benchmarks)
    assert all(item.measurement_as_of_date == date(2026, 8, 14) for item in result.benchmarks)
    assert all(item.pass_at_k == 1 for item in result.benchmarks)
    assert {
        (item.benchmark_id, item.number_of_tasks, item.number_of_trials)
        for item in result.benchmarks
    } == {("scicode", 288, 864), ("critpt", 70, 350)}
    assert {item.source_row_id for item in result.rejections} == {
        "critpt_external.csv:claude-fable-5_max",
        "scicode_external.csv:claude-fable-5_max",
    }


def test_epoch_arc_agi_2_accepts_only_exact_verified_max_rows(crosswalk) -> None:
    result = adapt_epoch_arc_agi_2_zip(
        SOURCES / "epoch-benchmark-data-2026-08-14.zip",
        crosswalk,
        source_id="epoch-benchmarks",
        artifact_id="epoch-benchmark-data-2026-08-14",
    )
    assert {
        item.model_id: item.value for item in result.benchmarks
    } == pytest.approx(
        {
            "claude-opus-5-max": 90.42,
            "gpt-5.6-sol-max": 92.5,
            "kimi-k3-max": 60.416666666666664,
        }
    )
    assert all(item.number_of_tasks == 120 and item.pass_at_k == 2 for item in result.benchmarks)
    assert all(item.tools_enabled is False for item in result.benchmarks)
    assert all(item.evaluation_date is None for item in result.benchmarks)
    assert {item.source_row_id for item in result.rejections} == {
        "arc_agi_2_external.csv:recKlOZaCgYdWkVtG",
        "arc_agi_2_external.csv:recMTvejGGEdgJHsM",
    }


def test_lab_release_facts_preserve_tariffs_and_claims(crosswalk) -> None:
    openai = adapt_lab_release_facts(SOURCES / "openai-release-facts-2026-08-14.yaml", crosswalk)
    assert len(openai.pricing) == 1
    assert openai.pricing[0].cached_input_per_million == 0.5
    assert openai.pricing[0].long_context_surcharge["threshold_input_tokens"] == 272000
    assert len(openai.release_claims) == 4
    assert all(
        item.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY
        for item in openai.release_claims
    )
    anthropic = adapt_lab_release_facts(
        SOURCES / "anthropic-release-facts-2026-08-14.yaml", crosswalk
    )
    assert {item.cache_write_1h_per_million for item in anthropic.pricing} == {10.0, 20.0}


def test_gap_report_counts_every_configured_model_benchmark_cell(
    pilot_dataset, pilot_config
) -> None:
    report = pilot_gap_report(pilot_dataset, pilot_config)
    assert len(report["capability_cells"]) == len(pilot_dataset.models) * len(
        pilot_config.benchmarks
    )
    assert sum(report["capability_cell_counts"].values()) == 70
    assert all(report["pricing_record_ids"].values())
    assert any(
        str(pilot_config.eligibility.minimum_capability_domains) in blocker
        for blocker in report["headline_blockers"]
    )
    assert any("claude-fable-5-max" in blocker for blocker in report["headline_blockers"])


def test_reviewed_adapter_rejects_schema_drift(monkeypatch, crosswalk) -> None:
    raw = yaml.safe_load((SOURCES / "deepswe-reviewed-facts-2026-08-13.yaml").read_text())
    del raw["rows"][0]["pass_rate"]
    monkeypatch.setattr("umi.adapters.reviewed.load_yaml", lambda path: raw)
    with pytest.raises(KeyError, match="pass_rate"):
        adapt_deepswe_facts("offline-malformed-artifact.yaml", crosswalk)


def test_overlap_cycles_and_unrestricted_double_count_are_rejected(pilot_config) -> None:
    reverse = OverlapEdge(
        source="hle",
        target="aa-intelligence-v4.1",
        relation=OverlapRelation.DERIVED_FROM,
        evidence="adversarial cycle",
    )
    overlap = pilot_config.overlap.model_copy(
        update={"edges": (*pilot_config.overlap.edges, reverse)}
    )
    with pytest.raises(ValidationError, match="acyclic"):
        ProjectConfig.model_validate({**pilot_config.model_dump(mode="python"), "overlap": overlap})

    double_count_overlap = pilot_config.overlap.model_copy(
        update={
            "signals": (
                SignalPolicy(
                    id="aggregate",
                        role=SignalRole.TASK,
                    disposition=ScoringDisposition.SCORED,
                    budget_group="aggregate-budget",
                ),
                SignalPolicy(
                    id="constituent",
                    role=SignalRole.TASK,
                    disposition=ScoringDisposition.SCORED,
                    budget_group="constituent-budget",
                ),
            ),
            "edges": (
                OverlapEdge(
                    source="aggregate",
                    target="constituent",
                    relation=OverlapRelation.CONTAINS,
                    evidence="known containment",
                ),
            ),
        }
    )
    with pytest.raises(ValidationError, match="share a budget"):
        ProjectConfig.model_validate(
            {**pilot_config.model_dump(mode="python"), "overlap": double_count_overlap}
        )


def test_documented_overlap_edges_cover_known_composites(pilot_config) -> None:
    edges = {(item.source, item.target, item.relation) for item in pilot_config.overlap.edges}
    assert ("epoch-eci", "deepswe-v1.1", OverlapRelation.CONTAINS) in edges
    assert ("epoch-eci", "arc-agi-2", OverlapRelation.CONTAINS) in edges
    assert ("arena-agent", "arena-agent-signals", OverlapRelation.CONTAINS) in edges
    assert ("aa-intelligence-v4.1", "hle", OverlapRelation.CONTAINS) in edges


def test_fixed_family_budgets_and_source_ablation(pilot_dataset, pilot_config) -> None:
    budgets = family_budget_snapshot(pilot_config)
    assert budgets[
        next(domain for domain in budgets if domain.value == "software_engineering")
    ] == {
        "deepswe-v1.1": 0.60,
        "terminalbench-2.1": 0.25,
        "scicode": 0.15,
        "legacy-aa-coding-index": 0.0,
    }
    scenarios = analyze_pilot_sensitivity(pilot_dataset, pilot_config)
    assert {item.scenario for item in scenarios} >= {
        "equal_family",
        "ablate_deepswe-v1.1-2026-08-13",
        "ablate_arena-agent-2026-08-14",
    }
    assert all(item.headline_overall is None for item in scenarios)
    assert family_budget_snapshot(pilot_config) == budgets
    fable_equal = next(
        item
        for item in scenarios
        if item.scenario == "equal_family" and item.model_id == "claude-fable-5-max"
    )
    assert not fable_equal.scenario_informative
    assert fable_equal.scale_changed
    assert not fable_equal.score_change_comparable
    epoch_ablation = next(
        item
        for item in scenarios
        if item.scenario == "ablate_epoch-benchmark-data-2026-08-14"
        and item.model_id == "claude-opus-5-max"
    )
    assert epoch_ablation.support_changed
    assert epoch_ablation.scale_changed
    assert not epoch_ablation.score_change_comparable
    assert epoch_ablation.raw_score_change is not None


def test_pilot_pareto_abstains_across_incomparable_capability_scales(
    pilot_dataset, pilot_config
) -> None:
    from analysis.pareto_metrics import pareto_dimensions

    report = pareto_dimensions(pilot_dataset, score_dataset(pilot_dataset, pilot_config))
    assert report["status"] == "insufficient_common_support"
    assert report["results"] == []


def test_publication_gates_and_real_evidence_label(pilot_dataset, pilot_config) -> None:
    results = {item.model_id: item for item in score_dataset(pilot_dataset, pilot_config)}
    assert set(results) == {
        "claude-opus-5-max",
        "claude-fable-5-max",
        "gpt-5.6-sol-max",
        "kimi-k3-max",
        "glm-5.2-max",
    }
    assert all(
        item.publication_label == "real evidence — model-specific partial estimate"
        for item in results.values()
    )
    assert all(item.headline_overall is None and not item.eligible for item in results.values())
    assert {
        item.model_id: item.coverage.capability_absolute_weighted for item in results.values()
    } == {
        "claude-fable-5-max": 0.165,
        "claude-opus-5-max": 0.49375,
        "glm-5.2-max": 0.35625,
        "gpt-5.6-sol-max": 0.49375,
        "kimi-k3-max": 0.49375,
    }
    assert {
        item.model_id: item.capability.score for item in results.values()
    } == pytest.approx(
        {
            "claude-fable-5-max": 50.0,
            "claude-opus-5-max": 76.9620253164557,
            "glm-5.2-max": 0.0,
            "gpt-5.6-sol-max": 82.27848101265822,
            "kimi-k3-max": 26.83544303797468,
        }
    )
    assert {
        item.model_id: item.efficiency.score for item in results.values()
    } == pytest.approx(
        {
            "claude-fable-5-max": 50.0,
            "claude-opus-5-max": 41.66666666666667,
            "glm-5.2-max": 0.0,
            "gpt-5.6-sol-max": 100.0,
            "kimi-k3-max": 58.333333333333336,
        }
    )
    assert all(item.efficiency.coverage == pytest.approx(0.045) for item in results.values())
    assert all(item.economics.score is None for item in results.values())
    assert all(item.economics.evidence_profile is None for item in results.values())
    assert all(item.economics.score_scale_id is None for item in results.values())
    assert all(
        item.efficiency.comparability_status == "directly_comparable"
        and item.economics.comparability_status == "insufficient_common_support"
        for item in results.values()
    )
    assert any("release date" in item for item in results["claude-fable-5-max"].diagnostics)


def test_diagnostic_evidence_changes_complete_not_scored_fingerprint(
    pilot_dataset, pilot_config
) -> None:
    baseline = {item.model_id: item for item in score_dataset(pilot_dataset, pilot_config)}
    diagnostic = pilot_dataset.external_indexes[0]
    changed = pilot_dataset.model_copy(
        update={
            "external_indexes": (
                diagnostic.model_copy(update={"value": diagnostic.value + 1}),
                *pilot_dataset.external_indexes[1:],
            ),
            "complete_audit_fingerprint": "f" * 64,
        }
    )
    changed_results = {item.model_id: item for item in score_dataset(changed, pilot_config)}
    assert dataset_fingerprint(changed, pilot_config) != dataset_fingerprint(
        pilot_dataset, pilot_config
    )
    assert {item.scored_data_fingerprint for item in baseline.values()} == {
        item.scored_data_fingerprint for item in changed_results.values()
    }
