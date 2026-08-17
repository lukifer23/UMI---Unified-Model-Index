from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from umi.edition import GOVERNED_EDITION_ID, GOVERNED_PUBLIC_INDEX, load_public_edition_config
from umi.feasibility import validate_public_edition_feasibility
from umi.identity import load_public_identities
from umi.public import SERIES, score_public_edition
from umi.public_blockers import PublicEvidenceBlocker, build_blocker_report
from umi.public_bundle import load_public_scoring_bundle
from umi.public_candidates import (
    PublicCandidateAudit,
    PublicCandidateAuditReport,
    audit_named_candidates,
)
from umi.public_certificate import build_public_certificate, overlapping_pairs, verify_epoch_zip
from umi.public_governance import source_concentration
from umi.public_sensitivity import WEIGHT_HYPOTHESES, quantify_weight_sensitivity
from umi.public_uncertainty import quantify_public_uncertainty
from umi.public_validate import validate_public_artifacts, validate_public_scores

V04_PILOTS = {
    "claude-opus-5-max",
    "claude-fable-5-max",
    "gpt-5.6-sol-max",
    "kimi-k3-max",
    "glm-5.2-max",
}


def test_v05_policy_is_feasible_and_expands_identities() -> None:
    config = load_public_edition_config(edition="v0.5")
    validate_public_edition_feasibility(config)
    assert config.edition_id == GOVERNED_EDITION_ID
    assert config.release_class == GOVERNED_PUBLIC_INDEX
    identities = load_public_identities(edition="v0.5")
    assert {item.entity_id for item in identities} == V04_PILOTS | {
        "gemini-3.6-flash-high",
        "gpt-5.4-2026-03-05-xhigh",
    }


def test_governed_public_bundle_binds_typed_zip_evidence() -> None:
    bundle = load_public_scoring_bundle(edition_name="v0.5")
    assert bundle.release_class == GOVERNED_PUBLIC_INDEX
    assert bundle.source_artifact_sha256 == verify_epoch_zip()
    assert [item.series_id for item in bundle.series] == [spec["id"] for spec in SERIES]
    identities = {item.entity_id for item in load_public_identities(edition="v0.5")}
    assert set(bundle.entity_ids) == identities
    for contract in bundle.series:
        assert set(contract.accepted_entity_ids) == identities
        assert contract.anchor_n >= 8
        assert all(
            item.source_artifact_sha256 == bundle.source_artifact_sha256
            for item in contract.records
        )
    again = load_public_scoring_bundle(edition_name="v0.5")
    assert again.evidence_fingerprint == bundle.evidence_fingerprint


def test_v05_reproduces_v04_pilot_scores() -> None:
    v04 = score_public_edition(edition_name="v0.4")
    v05 = score_public_edition(edition_name="v0.5")
    assert v05["publication_state"] == "published"
    assert len(v05["models"]) == 7
    scored = {item["entity_id"] for item in v05["models"]}
    assert "gpt-5.6-terra-max" not in scored
    assert "claude-sonnet-5-max" not in scored
    left = {item["entity_id"]: item["umi_public"] for item in v04["models"]}
    right = {item["entity_id"]: item["umi_public"] for item in v05["models"]}
    for entity_id in V04_PILOTS:
        assert left[entity_id] == right[entity_id]


def test_v05_validation_and_partial_intervals() -> None:
    payload = score_public_edition(edition_name="v0.5")
    report = validate_public_scores(payload, edition_name="v0.5")
    assert report["valid"] is True
    uncertainty = quantify_public_uncertainty(payload, edition_name="v0.5", draws=128)
    by_id = {item["entity_id"]: item for item in uncertainty["models"]}
    for entity_id, item in by_id.items():
        assert item["interval_low"] <= payload_score(payload, entity_id)
        assert payload_score(payload, entity_id) <= item["interval_high"]
        assert item["rank_low"] <= item["rank_high"]
        assert item["interval_status"] == "partial_source_interval"
        assert "epoch-scicode" in item["series_without_intervals"]
    assert uncertainty["family_ablations"]
    certificate = build_public_certificate(payload, report, uncertainty)
    assert certificate["status"] == "published_governed_index"
    assert certificate["source_artifact_sha256"] == verify_epoch_zip()
    assert certificate["result_fingerprint"]
    assert certificate["result_fingerprint"] != payload["scored_data_fingerprint"]
    sol = next(item for item in certificate["models"] if item["entity_id"] == "gpt-5.6-sol-max")
    assert sol["indistinguishable_from"] == []
    cluster = {
        item["entity_id"]
        for item in certificate["models"]
        if item["entity_id"]
        in {
            "claude-opus-5-max",
            "glm-5.2-max",
            "gemini-3.6-flash-high",
            "gpt-5.4-2026-03-05-xhigh",
            "claude-fable-5-max",
        }
        and item["indistinguishable_from"]
    }
    assert "claude-opus-5-max" in cluster
    pairs = overlapping_pairs(certificate["models"])
    assert pairs


def test_named_candidates_are_diagnostic_abstentions() -> None:
    identities = {item.entity_id for item in load_public_identities(edition="v0.5")}
    report = audit_named_candidates()
    assert report["headline_additions"] == []
    assert report["source_artifact_sha256"] == verify_epoch_zip()
    by_id = {item["candidate_id"]: item for item in report["candidates"]}
    assert set(by_id) == {"grok-4.5-high", "gemini-3.1-pro-preview"}
    grok = by_id["grok-4.5-high"]
    gemini = by_id["gemini-3.1-pro-preview"]
    assert grok["missing_series"] == ["epoch-weirdml", "weirdml-cost-per-run"]
    assert gemini["missing_series"] == ["weirdml-cost-per-run"]
    assert grok["notes"] == []
    assert gemini["notes"] == [
        "gemini-3.1-pro-preview has WeirdML Cost per run=1.36 but is excluded "
        "from the Access high-effort suffix panel"
    ]
    for item in (grok, gemini):
        assert item["headline_eligible"] is False
        assert item["status"] == "insufficient_common_support"
        assert item["umi_public"] is None
        assert item["candidate_id"] not in identities
        assert "diagnostic candidate certificate" in item["publication_label"]


def test_candidate_audit_rejects_invented_scores() -> None:
    live = audit_named_candidates()["candidates"][0]
    with pytest.raises(ValidationError, match="must not invent umi_public"):
        PublicCandidateAudit.model_validate({**live, "umi_public": 55.0})
    with pytest.raises(ValidationError, match="cannot be headline eligible"):
        PublicCandidateAudit.model_validate(
            {**live, "headline_eligible": True, "status": "published"}
        )
    with pytest.raises(ValidationError, match="must abstain"):
        PublicCandidateAudit.model_validate({**live, "status": "published"})
    report = audit_named_candidates()
    with pytest.raises(ValidationError, match="headline_additions must match"):
        PublicCandidateAuditReport.model_validate(
            {**report, "headline_additions": ["grok-4.5-high"]}
        )


def test_committed_candidate_audits_match_live() -> None:
    live = audit_named_candidates()
    root = Path(__file__).resolve().parents[1] / "data" / "editions" / "v0.5" / "processed"
    stored = json.loads((root / "candidate-audits.json").read_text(encoding="utf-8"))
    assert stored == live
    for item in live["candidates"]:
        path = root / f"candidate-{item['candidate_id']}.json"
        assert json.loads(path.read_text(encoding="utf-8")) == item
    audit = validate_public_artifacts("v0.5")
    assert audit["valid"] is True


def test_blocker_report_is_precise_and_unscored() -> None:
    report = build_blocker_report()
    by_id = {item["blocker_id"]: item for item in report["blockers"]}
    assert report["headline_published"] is True
    assert by_id["candidate-grok-4.5-high"]["missing_series"] == [
        "epoch-weirdml",
        "weirdml-cost-per-run",
    ]
    assert by_id["candidate-gemini-3.1-pro-preview"]["missing_series"] == [
        "weirdml-cost-per-run"
    ]
    for blocker_id in (
        "near-miss-gpt-5.6-terra-max",
        "near-miss-gpt-5.6-luna-max",
        "near-miss-claude-sonnet-5-max",
        "near-miss-claude-opus-4-8-max",
    ):
        assert by_id[blocker_id]["missing_series"] == [
            "epoch-weirdml",
            "weirdml-cost-per-run",
        ]
    assert "construct-billed-economics" in by_id
    assert "construct-interactive-latency" in by_id
    for item in report["blockers"]:
        assert item["umi_public"] is None
        assert item["urls_investigated"]
        assert item["sources_investigated"]
        assert item["resolving_evidence"]
    with pytest.raises(ValidationError, match="must not invent umi_public"):
        PublicEvidenceBlocker.model_validate({**report["blockers"][0], "umi_public": 50.0})


def test_source_concentration_stays_inside_the_cap() -> None:
    concentration = source_concentration(edition_name="v0.5")
    capability = concentration["components"]["capability"]
    assert capability["cap_applied"] is True
    assert capability["source_shares"]["epoch"] == pytest.approx(0.35)
    assert capability["largest_share"] == pytest.approx(0.35)
    assert concentration["components"]["operational_efficiency"]["cap_applied"] is False
    assert concentration["components"]["access_economics"]["cap_applied"] is False


def test_weight_sensitivity_is_diagnostic_and_preserves_headline() -> None:
    payload = score_public_edition(edition_name="v0.5")
    report = quantify_weight_sensitivity(payload)
    assert report["status"] == "diagnostic"
    assert report["headline_unchanged"] is True
    assert [item["name"] for item in WEIGHT_HYPOTHESES] == report["hypotheses"]
    baseline = next(item for item in report["scenarios"] if item["name"] == "baseline")
    ranked = sorted(payload["models"], key=lambda row: row["rank"])
    published = [item["entity_id"] for item in ranked]
    assert baseline["order"] == published
    by_id = {item["entity_id"]: item for item in payload["models"]}
    for row in baseline["models"]:
        assert row["diagnostic_public"] == pytest.approx(by_id[row["entity_id"]]["umi_public"])


def test_committed_blocker_report_matches_live() -> None:
    live = build_blocker_report()
    root = Path(__file__).resolve().parents[1] / "data" / "editions" / "v0.5" / "processed"
    stored = json.loads((root / "blocker-report.json").read_text(encoding="utf-8"))
    assert stored == live
    assert (root / "edition-manifest.json").is_file()
    assert (root / "source-concentration.json").is_file()


def test_incomplete_candidate_identity_fails_closed() -> None:
    identities = load_public_identities(edition="v0.5")
    grok = identities[0].model_copy(
        update={
            "entity_id": "grok-4.5-high",
            "developer": "xAI",
            "named_release": "Grok 4.5",
            "effort_setting": "high",
            "reasoning_mode": "high",
            "primary_target": "grok-4.5",
        }
    )
    with pytest.raises(ValueError, match="required public series failed"):
        score_public_edition(edition_name="v0.5", identities=(*identities, grok))


def payload_score(payload: dict[str, object], entity_id: str) -> float:
    models = payload["models"]
    assert isinstance(models, list)
    match = next(item for item in models if item["entity_id"] == entity_id)
    value = match["umi_public"]
    assert isinstance(value, float)
    return value
