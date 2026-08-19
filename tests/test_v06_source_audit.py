from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

import umi.v06_source_audit as source_audit
from analysis.v06_source_audit_dashboard import (
    build_v06_source_audit_dashboard,
    render_v06_source_audit_dashboard_html,
    write_v06_source_audit_dashboard,
)
from umi.v06_source_audit import (
    CURRENT_FIVE,
    SourceAuditConfig,
    V06SourceAuditReport,
    build_v06_source_audit,
    load_v06_source_audit_config,
    validate_v06_source_audit,
    write_v06_source_audit,
)


def test_v06_source_audit_is_deterministic_and_withholds_headline() -> None:
    first = build_v06_source_audit()
    second = build_v06_source_audit()
    assert first == second
    assert first["target_cohort"] == list(CURRENT_FIVE)
    assert first["headline_eligible"] is False
    assert first["headline_overall"] is None
    assert first["publication_state"] == "verified_abstention"
    assert "provider-billed-economics" in first["unresolved_requirement_ids"]
    assert "hierarchical-bootstrap" in first["unresolved_requirement_ids"]
    assert first["rootcausebench_review"]["scoring_disposition"] == "diagnostic_only"


def test_v06_source_audit_checks_real_artifacts_and_rights() -> None:
    report = build_v06_source_audit()
    artifacts = {item["artifact_id"]: item for item in report["source_artifacts"]}
    assert artifacts["epoch-benchmark-data-2026-08-14"]["checksum_valid"] is True
    assert artifacts["epoch-benchmark-data-2026-08-14"]["redistribution_scope"] == "full_artifact"
    assert artifacts["deepswe-v1.1-2026-08-13"]["checksum_valid"] is True
    assert artifacts["deepswe-v1.1-2026-08-13"]["redistribution_scope"] == "facts_only"
    requirements = {item["requirement_id"]: item for item in report["requirements"]}
    assert requirements["common-core-capability"]["passes"] is True
    assert requirements["rootcausebench-v3-final-trial-integrity"]["passes"] is True
    assert requirements["success-adjusted-efficiency"]["passes"] is False
    efficiency_failures = requirements["success-adjusted-efficiency"]["failures"]
    assert any("facts_only" in item for item in efficiency_failures)


def test_v06_config_is_fixed_to_the_exact_cohort_and_cutoff() -> None:
    config = load_v06_source_audit_config()
    assert config.target_cohort == CURRENT_FIVE
    assert config.evidence_snapshot_cutoff == "2026-08-19T00:00:00Z"


def test_v06_config_rejects_cohort_or_cutoff_drift() -> None:
    config = load_v06_source_audit_config()
    cohort_drift = config.model_dump(mode="json")
    cohort_drift["target_cohort"] = list(reversed(CURRENT_FIVE))
    with pytest.raises(ValidationError, match="target cohort"):
        SourceAuditConfig.model_validate(cohort_drift)
    cutoff_drift = config.model_dump(mode="json")
    cutoff_drift["evidence_snapshot_cutoff"] = "2026-08-20T00:00:00Z"
    with pytest.raises(ValidationError, match="cutoff"):
        SourceAuditConfig.model_validate(cutoff_drift)


def test_v06_checksum_mismatch_blocks_an_otherwise_admitted_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source_audit, "_sha256", lambda _path: "0" * 64)
    report = source_audit.build_v06_source_audit()
    requirements = {item["requirement_id"]: item for item in report["requirements"]}
    assert requirements["common-core-capability"]["passes"] is False
    capability_failures = requirements["common-core-capability"]["failures"]
    assert any("checksum is not verified" in item for item in capability_failures)


def test_v06_report_rejects_a_headline_or_resolved_stub() -> None:
    report = build_v06_source_audit()
    invented = deepcopy(report)
    invented["headline_eligible"] = True
    with pytest.raises(ValidationError, match="must not manufacture"):
        V06SourceAuditReport.model_validate(invented)
    resolved = deepcopy(report)
    resolved["unresolved_requirement_ids"] = []
    with pytest.raises(ValidationError, match="must replace"):
        V06SourceAuditReport.model_validate(resolved)


def test_v06_writers_and_validation_are_deterministic(tmp_path: Path) -> None:
    report = write_v06_source_audit(tmp_path)
    dashboard = write_v06_source_audit_dashboard(tmp_path, report=report)
    assert (tmp_path / "public-source-audit.json").is_file()
    assert (tmp_path / "public-source-audit-dashboard.json").is_file()
    html = (tmp_path / "public-source-audit-dashboard.html").read_text(encoding="utf-8")
    assert report["source_audit_fingerprint"] in html
    assert "Headline Overall is withheld" in html
    assert {item["id"] for item in dashboard["charts"]} == {
        "gate_progress",
        "source_requirements",
        "rootcausebench_pass_rate",
    }


def test_v06_dashboard_is_renderable_without_score_invention() -> None:
    dashboard = build_v06_source_audit_dashboard(build_v06_source_audit())
    assert dashboard["headline_overall"] is None
    assert dashboard["headline_eligible"] is False
    assert "v0.5 partial" in render_v06_source_audit_dashboard_html(dashboard)


def test_committed_v06_audit_matches_live() -> None:
    report = build_v06_source_audit()
    root = Path(__file__).resolve().parents[1]
    stored = json.loads(
        (root / "data" / "editions" / "v0.6" / "processed" / "public-source-audit.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored == report
    assert validate_v06_source_audit()["valid"] is True
