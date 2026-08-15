from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from analysis.claims import calibrate_release_claims
from analysis.compare import common_capability_comparison
from analysis.correlations import benchmark_correlations
from analysis.gaps import pilot_gap_report
from analysis.pareto_metrics import pareto_dimensions
from analysis.pilot_dashboard import build_pilot_dashboard
from analysis.pilot_sensitivity import analyze_pilot_sensitivity
from analysis.sensitivity import analyze_sensitivity
from analysis.uncertainty import source_bound_capability_sensitivity
from umi.adapters import (
    adapt_aa_facts,
    adapt_aa_gdpval_facts,
    adapt_aa_lcr_facts,
    adapt_aa_tau3_facts,
    adapt_arena_json,
    adapt_cursorbench_facts,
    adapt_deepswe_facts,
    adapt_epoch_benchmarks_zip,
    adapt_epoch_csv,
    adapt_lab_release_facts,
    assemble_pilot_dataset,
)
from umi.bundle import ScoringBundle, build_acceptance_manifest, validate_scoring_bundle
from umi.certificate import build_comparison_certificate
from umi.config import load_project_config
from umi.loading import load_model_crosswalk, load_source_registry
from umi.schemas import ModelConfiguration, ScoringDisposition
from umi.scoring import score_bundle
from umi.source_policy import overlap_report, source_readiness_matrix, validate_crosswalk
from umi.validation import validate_dataset, validate_source_registry

ROOT = Path(__file__).parents[1]
SOURCE_ROOT = ROOT / "data" / "sources" / "v0.3"
PILOT_ROOT = ROOT / "data" / "pilots" / "v0.3"
RAW_ROOT = PILOT_ROOT / "raw"
PROCESSED_ROOT = PILOT_ROOT / "processed"


def _hash(value: object) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def _write_yaml(path: Path, key: str, values: tuple[Any, ...]) -> None:
    payload = {key: [item.model_dump(mode="json", exclude_none=True) for item in values]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def main() -> None:
    models_raw = yaml.safe_load((RAW_ROOT / "models.yaml").read_text(encoding="utf-8"))
    models = TypeAdapter(tuple[ModelConfiguration, ...]).validate_python(models_raw["models"])
    crosswalk = load_model_crosswalk(SOURCE_ROOT / "crosswalk.yaml")
    registry = load_source_registry(ROOT / "data" / "sources" / "registry.yaml")
    results = (
        adapt_aa_facts(SOURCE_ROOT / "aa-reviewed-facts-2026-08-14.yaml", crosswalk),
        adapt_aa_facts(SOURCE_ROOT / "aa-hle-reviewed-facts-2026-08-14.yaml", crosswalk),
        adapt_aa_gdpval_facts(
            SOURCE_ROOT / "aa-gdpval-reviewed-facts-2026-08-15.yaml", crosswalk
        ),
        adapt_aa_tau3_facts(
            SOURCE_ROOT / "aa-tau3-reviewed-facts-2026-08-15.yaml", crosswalk
        ),
        adapt_aa_lcr_facts(
            SOURCE_ROOT / "aa-lcr-reviewed-facts-2026-08-15.yaml", crosswalk
        ),
        adapt_cursorbench_facts(
            SOURCE_ROOT / "cursorbench-reviewed-facts-2026-08-14.yaml", crosswalk
        ),
        adapt_epoch_csv(
            SOURCE_ROOT / "epoch-eci-benchmarks-2026-08-14.csv",
            crosswalk,
            source_id="epoch-eci",
            artifact_id="epoch-eci-matrix-2026-08-14",
        ),
        adapt_epoch_benchmarks_zip(
            SOURCE_ROOT / "epoch-benchmark-data-2026-08-14.zip",
            crosswalk,
            source_id="epoch-benchmarks",
            artifact_id="epoch-benchmark-data-2026-08-14",
        ),
        adapt_arena_json(
            SOURCE_ROOT / "arena-agent-2026-08-14.json",
            crosswalk,
            source_id="arena-agent",
            artifact_id="arena-agent-2026-08-14",
            upstream_revision="08dd89df7a8aa9df2ead3799f6422af4ad2e97a7",
            subset="agent",
        ),
        adapt_arena_json(
            SOURCE_ROOT / "arena-text-style-control-2026-08-14.json",
            crosswalk,
            source_id="arena-text",
            artifact_id="arena-text-2026-08-14",
            upstream_revision="08dd89df7a8aa9df2ead3799f6422af4ad2e97a7",
            subset="text_style_control",
        ),
        adapt_deepswe_facts(SOURCE_ROOT / "deepswe-reviewed-facts-2026-08-13.yaml", crosswalk),
        *(
            adapt_lab_release_facts(SOURCE_ROOT / filename, crosswalk)
            for filename in (
                "anthropic-release-facts-2026-08-14.yaml",
                "openai-release-facts-2026-08-14.yaml",
                "kimi-release-facts-2026-08-14.yaml",
                "zai-release-facts-2026-08-14.yaml",
            )
        ),
    )
    dataset = assemble_pilot_dataset(models, results)
    relevant_ids = {entry.source_artifact_id for entry in crosswalk.entries}
    snapshots = [
        item.model_dump(mode="json") for item in registry.snapshots if item.id in relevant_ids
    ]
    complete_payload = {
        "snapshots": snapshots,
        "crosswalk": crosswalk.model_dump(mode="json"),
        "adapter_results": [item.model_dump(mode="json") for item in results],
    }
    scored_records = [
        item.model_dump(mode="json")
        for item in (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
        if item.scoring_disposition == ScoringDisposition.SCORED
    ]
    scored_artifacts = {item["source_artifact_id"] for item in scored_records}
    scored_payload = {
        "snapshots": [item for item in snapshots if item["id"] in scored_artifacts],
        "exact_crosswalk": [
            item.model_dump(mode="json")
            for item in crosswalk.entries
            if item.source_artifact_id in scored_artifacts and item.status.value == "exact"
        ],
        "accepted_scoring_records": scored_records,
    }
    adapter_versions = tuple(
        sorted(
            {
                item.adapter_id
                for item in results
                if any(
                    record.scoring_disposition == ScoringDisposition.SCORED
                    for record in (
                        *item.benchmarks,
                        *item.efficiency,
                        *item.task_economics,
                    )
                )
            }
        )
    )
    dataset = dataset.model_copy(
        update={
            "scored_audit_fingerprint": _hash(scored_payload),
            "complete_audit_fingerprint": _hash(complete_payload),
            "adapter_versions": adapter_versions,
        }
    )
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    _write_yaml(RAW_ROOT / "benchmarks.yaml", "measurements", dataset.benchmarks)
    _write_yaml(RAW_ROOT / "pricing.yaml", "pricing", dataset.pricing)
    _write_yaml(RAW_ROOT / "task_efficiency.yaml", "measurements", dataset.efficiency)
    _write_yaml(RAW_ROOT / "task_economics.yaml", "measurements", dataset.task_economics)
    _write_yaml(RAW_ROOT / "external_indexes.yaml", "measurements", dataset.external_indexes)
    _write_yaml(RAW_ROOT / "release_claims.yaml", "claims", dataset.release_claims)
    (RAW_ROOT / "audit.yaml").write_text(
        yaml.safe_dump(
            {
                "scored_audit_fingerprint": dataset.scored_audit_fingerprint,
                "complete_audit_fingerprint": dataset.complete_audit_fingerprint,
                "adapter_versions": list(adapter_versions),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report = {
        "label": "real evidence — model-specific partial estimate",
        "sources": [item.model_dump(mode="json") for item in results],
        "scored_audit_fingerprint": dataset.scored_audit_fingerprint,
        "complete_audit_fingerprint": dataset.complete_audit_fingerprint,
    }
    (PROCESSED_ROOT / "adaptation-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    config = load_project_config(ROOT / "config")
    bundle_errors = validate_scoring_bundle(
        dataset,
        config,
        registry,
        ROOT / "data" / "sources" / "registry.yaml",
        crosswalk,
    )
    if bundle_errors:
        raise ValueError("invalid scoring bundle: " + "; ".join(bundle_errors))
    data_report = validate_dataset(dataset, config)
    registry_report = validate_source_registry(
        registry, ROOT / "data" / "sources" / "registry.yaml", dataset
    )
    crosswalk_report = validate_crosswalk(crosswalk, dataset, registry)
    acceptance_manifest = build_acceptance_manifest(dataset, registry)
    source_report = {
        "schema_valid": data_report.schema_valid,
        "scored_inputs_ready": data_report.scored_inputs_ready,
        "strict_audit_valid": not registry_report.errors and crosswalk_report.valid,
        "headline_eligible": None,
        "crosswalk_valid": crosswalk_report.valid,
        "source_errors": list(registry_report.errors),
        "crosswalk_errors": list(crosswalk_report.errors),
        "acceptance_manifest": acceptance_manifest.model_dump(mode="json"),
        "readiness": [item.model_dump(mode="json") for item in source_readiness_matrix(dataset)],
    }
    (PROCESSED_ROOT / "source-readiness.json").write_text(
        json.dumps(source_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    bundle = ScoringBundle(
        dataset=dataset,
        config=config,
        source_registry=registry,
        crosswalk=crosswalk,
        registry_path=ROOT / "data" / "sources" / "registry.yaml",
        acceptance_manifest=acceptance_manifest,
    )
    scoring_results = score_bundle(bundle)
    estimates = [item.model_dump(mode="json") for item in scoring_results]
    (PROCESSED_ROOT / "model-specific-partial-estimates.json").write_text(
        json.dumps(estimates, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (PROCESSED_ROOT / "overall-sensitivity.json").write_text(
        json.dumps(
            [asdict(item) for item in analyze_sensitivity(scoring_results, config)],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "pilot-sensitivity.json").write_text(
        json.dumps(
            [asdict(item) for item in analyze_pilot_sensitivity(dataset, config)],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "correlations.json").write_text(
        json.dumps(
            [
                asdict(item)
                for item in benchmark_correlations(
                    dataset, config.normalization.correlation_min_overlap, config
                )
            ],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "pareto.json").write_text(
        json.dumps(
            pareto_dimensions(dataset, scoring_results),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "overlap.json").write_text(
        json.dumps(overlap_report(config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "source-bound-uncertainty.json").write_text(
        json.dumps(source_bound_capability_sensitivity(dataset, config), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "release-claim-calibration.json").write_text(
        json.dumps(calibrate_release_claims(dataset), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    gap_report = pilot_gap_report(dataset, config)
    (PROCESSED_ROOT / "pilot-gap-report.json").write_text(
        json.dumps(gap_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "pilot-dashboard.json").write_text(
        json.dumps(build_pilot_dashboard(dataset, estimates, gap_report), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    five_models = tuple(model.id for model in models)
    three_models = ("claude-opus-5-max", "kimi-k3-max", "glm-5.2-max")
    for name, model_ids in (
        ("common-evidence-five-model-comparison.json", five_models),
        ("common-evidence-three-model-comparison.json", three_models),
    ):
        comparison = common_capability_comparison(dataset, config, model_ids)
        (PROCESSED_ROOT / name).write_text(
            json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    certificate = build_comparison_certificate(bundle, three_models)
    (PROCESSED_ROOT / "comparison-certificate-three-model.json").write_text(
        json.dumps(certificate.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
