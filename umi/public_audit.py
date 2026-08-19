"""Typed publication audit for the governed public edition.

This module is presentation and release-governance work only.  It reads the
already-built governed scoring artifacts and the legacy governed result
artifacts; it never rescored evidence, changes eligibility, or invents a
headline value.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from umi.config import load_project_config
from umi.edition import ConfigModel
from umi.public import ROOT
from umi.public_blockers import build_blocker_report

PUBLIC_AUDIT_VERSION = "umi-public-audit-v0.1"
CURRENT_FIVE = (
    "claude-fable-5-max",
    "claude-opus-5-max",
    "gpt-5.6-sol-max",
    "kimi-k3-max",
    "glm-5.2-max",
)


class GateAssessment(ConfigModel):
    observed: float = Field(ge=0)
    required: float = Field(ge=0)
    passes: bool
    unit: str


class PublicationAuditModel(ConfigModel):
    entity_id: str
    publication_scope: str
    governed_score: float | None = None
    headline_overall: float | None = None
    headline_eligible: bool
    confidence: str
    capability_coverage: float = Field(ge=0, le=1)
    efficiency_coverage: float = Field(ge=0, le=1)
    economics_coverage: float = Field(ge=0, le=1)
    overall_coverage: float = Field(ge=0, le=1)
    capability_domains_represented: int = Field(ge=0)
    efficiency_workloads_represented: int = Field(ge=0)
    economics_workloads_represented: int = Field(ge=0)
    gates: dict[str, GateAssessment]
    blockers: tuple[str, ...]
    diagnostics: tuple[str, ...]


class PublicationAuditReport(ConfigModel):
    report_version: str
    edition_id: str
    publication_state: str
    publication_scope: str
    headline_eligible: bool
    headline_overall: float | None
    target_cohort: tuple[str, ...]
    source_artifacts: dict[str, str]
    evidence_counts: dict[str, int]
    gates: dict[str, GateAssessment]
    models: tuple[PublicationAuditModel, ...]
    blockers: tuple[str, ...]
    blocker_count: int = Field(ge=0)
    narrative: tuple[str, ...]
    scored_data_fingerprint: str
    complete_audit_fingerprint: str | None = None


def _read_json(path: Path) -> dict[str, Any] | list[Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, (dict, list)):
        raise ValueError(f"{path} must contain a JSON object or array")
    return cast(dict[str, Any] | list[Any], loaded)


def _legacy_rows() -> dict[str, dict[str, Any]]:
    path = ROOT / "data" / "pilots" / "v0.3" / "processed" / "model-specific-partial-estimates.json"
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a list of scoring results")
    rows = {str(item["model_id"]): item for item in payload}
    missing = [model_id for model_id in CURRENT_FIVE if model_id not in rows]
    if missing:
        raise ValueError(f"governed audit is missing target cohort rows: {missing}")
    return rows


def _governed_scores(
    path: Path | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    source = path or ROOT / "data" / "editions" / "v0.5" / "processed" / "model-scores.json"
    loaded = payload if payload is not None else _read_json(source)
    if not isinstance(loaded, dict):
        raise ValueError(f"{source} must contain a scoring payload")
    return {str(item["entity_id"]): item for item in loaded.get("models", ())}


def _gap_counts() -> dict[str, int]:
    path = ROOT / "data" / "pilots" / "v0.3" / "processed" / "pilot-gap-report.json"
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a gap report")
    counts = payload.get("capability_cell_counts", {})
    if not isinstance(counts, dict):
        raise ValueError("pilot gap report has no capability_cell_counts mapping")
    return {
        "capability_ready_scored": int(counts.get("ready_scored", 0)),
        "capability_diagnostic_measurement": int(counts.get("diagnostic_measurement", 0)),
        "capability_diagnostic_reference": int(counts.get("diagnostic_reference", 0)),
        "capability_missing": int(counts.get("missing", 0)),
        "capability_cells_total": sum(int(value) for value in counts.values()),
    }


def _complete_audit_fingerprint() -> str | None:
    path = ROOT / "data" / "pilots" / "v0.3" / "processed" / "adaptation-report.json"
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain an adaptation report")
    value = payload.get("complete_audit_fingerprint")
    return str(value) if value is not None else None


def _gate(observed: float, required: float, unit: str) -> GateAssessment:
    return GateAssessment(
        observed=observed,
        required=required,
        passes=observed >= required,
        unit=unit,
    )


def _model_blockers(row: dict[str, Any], config: Any) -> tuple[str, ...]:
    coverage = row["coverage"]
    required = config.eligibility.minimum_component_coverage
    blockers: list[str] = []
    for component in ("capability", "efficiency", "economics"):
        observed = float(row[component]["coverage"])
        threshold = float(required[component])
        if observed < threshold:
            blockers.append(
                f"{component} coverage {observed:.3f} is below the {threshold:.3f} gate"
            )
    overall = float(row["overall_coverage"])
    if overall < config.eligibility.minimum_overall_coverage:
        blockers.append(
            f"overall coverage {overall:.3f} is below the "
            f"{config.eligibility.minimum_overall_coverage:.3f} gate"
        )
    efficiency_workload = float(coverage["efficiency_workload_weighted"])
    if efficiency_workload < config.eligibility.minimum_efficiency_workload_coverage:
        blockers.append(
            f"efficiency workload coverage {efficiency_workload:.3f} is below the "
            f"{config.eligibility.minimum_efficiency_workload_coverage:.3f} gate"
        )
    domains = int(coverage["capability_domains_represented"])
    if domains < config.eligibility.minimum_capability_domains:
        blockers.append(
            f"capability breadth {domains} domains is below the "
            f"{config.eligibility.minimum_capability_domains}-domain gate"
        )
    if not row["eligible"]:
        blockers.append("headline eligibility is false")
    return tuple(blockers)


def build_public_audit_report(
    payload: dict[str, Any] | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    if edition_name != "v0.5":
        raise ValueError("publication audit is a v0.5 governed surface")
    loaded_payload: dict[str, Any] | list[Any]
    if payload is None:
        score_path = ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json"
        loaded_payload = _read_json(score_path)
    else:
        loaded_payload = payload
    if not isinstance(loaded_payload, dict):
        raise ValueError("public audit requires a scoring payload")
    payload = loaded_payload
    config = load_project_config(ROOT / "config")
    legacy = _legacy_rows()
    scores = _governed_scores(payload=payload)
    target_rows: list[dict[str, Any]] = []
    for model_id in CURRENT_FIVE:
        row = legacy[model_id]
        public = scores.get(model_id, {})
        coverage = row["coverage"]
        gates = {
            "capability": _gate(
                float(row["capability"]["coverage"]),
                float(config.eligibility.minimum_component_coverage["capability"]),
                "fraction",
            ),
            "efficiency": _gate(
                float(row["efficiency"]["coverage"]),
                float(config.eligibility.minimum_component_coverage["efficiency"]),
                "fraction",
            ),
            "economics": _gate(
                float(row["economics"]["coverage"]),
                float(config.eligibility.minimum_component_coverage["economics"]),
                "fraction",
            ),
            "overall": _gate(
                float(row["overall_coverage"]),
                float(config.eligibility.minimum_overall_coverage),
                "fraction",
            ),
            "efficiency_workload": _gate(
                float(coverage["efficiency_workload_weighted"]),
                float(config.eligibility.minimum_efficiency_workload_coverage),
                "fraction",
            ),
            "capability_breadth": _gate(
                float(coverage["capability_domains_represented"]),
                float(config.eligibility.minimum_capability_domains),
                "domains",
            ),
        }
        target_rows.append(
            {
                "entity_id": model_id,
                "publication_scope": "governed_partial",
                "governed_score": public.get("umi_public"),
                "headline_overall": row.get("headline_overall"),
                "headline_eligible": bool(row["eligible"]),
                "confidence": str(row["confidence"]),
                "capability_coverage": float(row["capability"]["coverage"]),
                "efficiency_coverage": float(row["efficiency"]["coverage"]),
                "economics_coverage": float(row["economics"]["coverage"]),
                "overall_coverage": float(row["overall_coverage"]),
                "capability_domains_represented": int(coverage["capability_domains_represented"]),
                "efficiency_workloads_represented": int(
                    coverage["efficiency_workloads_represented"]
                ),
                "economics_workloads_represented": int(
                    coverage["economics_workloads_represented"]
                ),
                "gates": {name: item.model_dump(mode="json") for name, item in gates.items()},
                "blockers": _model_blockers(row, config),
                "diagnostics": tuple(str(item) for item in row.get("diagnostics", ())),
            }
        )
    blocker_report = build_blocker_report()
    blockers = tuple(str(item["blocker_id"]) for item in blocker_report["blockers"])
    counts = _gap_counts()
    component_coverage = {
        component: min(float(row[f"{component}_coverage"]) for row in target_rows)
        for component in ("capability", "efficiency", "economics")
    }
    overall_coverage = min(float(row["overall_coverage"]) for row in target_rows)
    minimum_components = config.eligibility.minimum_component_coverage
    gates = {
        "capability": _gate(
            counts["capability_ready_scored"] / counts["capability_cells_total"],
            float(minimum_components["capability"]),
            "fraction of configured cells",
        ),
        "efficiency": _gate(
            component_coverage["efficiency"],
            float(minimum_components["efficiency"]),
            "hierarchical workload coverage",
        ),
        "economics": _gate(
            component_coverage["economics"],
            float(minimum_components["economics"]),
            "hierarchical workload coverage",
        ),
        "overall": _gate(
            overall_coverage,
            float(config.eligibility.minimum_overall_coverage),
            "headline eligibility",
        ),
    }
    report = {
        "report_version": PUBLIC_AUDIT_VERSION,
        "edition_id": str(payload["edition_id"]),
        "publication_state": str(payload["publication_state"]),
        "publication_scope": "governed_partial",
        "headline_eligible": False,
        "headline_overall": None,
        "target_cohort": CURRENT_FIVE,
        "source_artifacts": {
            "governed_scores": "data/editions/v0.5/processed/model-scores.json",
            "legacy_scoring_results": (
                "data/pilots/v0.3/processed/model-specific-partial-estimates.json"
            ),
            "capability_gap_report": "data/pilots/v0.3/processed/pilot-gap-report.json",
            "adaptation_report": "data/pilots/v0.3/processed/adaptation-report.json",
            "blocker_report": "data/editions/v0.5/processed/blocker-report.json",
        },
        "evidence_counts": counts,
        "gates": {name: item.model_dump(mode="json") for name, item in gates.items()},
        "models": target_rows,
        "blockers": blockers,
        "blocker_count": len(blocker_report["blockers"]),
        "narrative": (
            "The seven v0.5 values are governed partial scores from complete common-core evidence.",
            "They are not headline Overall UMI scores because the configured Efficiency "
            "and Economics gates are not met.",
            "Access Economics is source-reported public task cost, not provider-billed "
            "task economics.",
            "The target cohort remains the current five exact configurations; missing or "
            "fallback evidence stays abstained.",
        ),
        "scored_data_fingerprint": str(payload["scored_data_fingerprint"]),
        "complete_audit_fingerprint": _complete_audit_fingerprint(),
    }
    return PublicationAuditReport.model_validate(report).model_dump(mode="json")


def render_public_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UMI Public v0.5 publication audit",
        "",
        "This is the release-governance companion to the governed partial score artifacts. "
        "It does not rescore evidence or turn a partial result into a headline.",
        "",
        f"- edition: `{report['edition_id']}`",
        f"- publication scope: `{report['publication_scope']}`",
        f"- headline eligible: `{str(report['headline_eligible']).lower()}`",
        f"- scored-data fingerprint: `{report['scored_data_fingerprint']}`",
        "",
        "## What is publishable",
        "",
        "The v0.5 common-core values are real, deterministic, source-bound scores for exact "
        "model configurations. They are published as governed partials. No `headline_overall` "
        "value or Overall rank is published; common-core order remains diagnostic and "
        "provenance-bound.",
        "",
        "## Gate status",
        "",
        "| Gate | Observed | Required | Result |",
        "|---|---:|---:|---|",
    ]
    for name, gate in report["gates"].items():
        observed = gate["observed"]
        required = gate["required"]
        if gate["unit"] == "domains":
            observed_text = f"{observed:.0f} domains"
            required_text = f"{required:.0f} domains"
        else:
            observed_text = f"{observed:.1%}"
            required_text = f"{required:.1%}"
        result = "pass" if gate["passes"] else "blocked"
        lines.append(f"| `{name}` | {observed_text} | {required_text} | **{result}** |")
    lines.extend(
        [
            "",
            "## Target-cohort coverage",
            "",
            "| Configuration | Governed partial | Capability | Efficiency | Economics | "
            "Confidence | Headline |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in report["models"]:
        score = "—" if row["governed_score"] is None else f"{row['governed_score']:.2f}"
        headline = "eligible" if row["headline_eligible"] else "withheld"
        lines.append(
            f"| `{row['entity_id']}` | {score} | {row['capability_coverage']:.1%} | "
            f"{row['efficiency_coverage']:.1%} | {row['economics_coverage']:.1%} | "
            f"{row['confidence']} | {headline} |"
        )
    lines.extend(
        [
            "",
            "## Evidence inventory",
            "",
            "Accepted Capability cells: **"
            f"{report['evidence_counts']['capability_ready_scored']} / "
            f"{report['evidence_counts']['capability_cells_total']}**. "
            f"Missing cells: **{report['evidence_counts']['capability_missing']}**. "
            "Diagnostic evidence is retained but does not count as scored coverage.",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in report["blockers"])
    lines.extend(
        [
            "",
            "The complete blocker details remain in `BLOCKER_REPORT.md`. Resolving a blocker "
            "requires exact identity, compatible cohort, readiness, rights, and preserved raw "
            "artifact evidence; no missing value is imputed.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_audit_report(
    output_dir: Path | None = None,
    *,
    payload: dict[str, Any] | None = None,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    report = build_public_audit_report(payload, edition_name=edition_name)
    (destination / "public-audit-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if output_dir is None:
        docs = ROOT / "docs" / "editions" / edition_name / "AUDIT_REPORT.md"
        docs.parent.mkdir(parents=True, exist_ok=True)
        docs.write_text(render_public_audit_markdown(report), encoding="utf-8")
    return report
