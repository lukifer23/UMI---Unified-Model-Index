"""Precise evidence blocker report. Does not invent scores or lower gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from umi.edition import GOVERNED_EDITION_ID, ConfigModel, load_public_edition_config
from umi.public import ROOT, _diagnostic_blockers, public_series_specs
from umi.public_candidates import (
    CANDIDATES,
    NEAR_MISS_CANDIDATES,
    _present_series,
    audit_named_candidates,
)
from umi.public_certificate import EPOCH_SHA256, verify_epoch_zip

BLOCKER_REPORT_VERSION = "umi-public-blocker-report-v0.5"
EPOCH_ZIP_URL = "https://epoch.ai/data/benchmark_data.zip"
EPOCH_HUB_URL = "https://epoch.ai/benchmarks/about"
WEIRDML_URL = "https://htihle.github.io/weirdml.html"
DEEPSWE_URL = "https://deepswe.datacurve.ai/"
DEEPSWE_LEDGER_URL = "https://deepswe.datacurve.ai/artifacts/v1.1/trials.json"
LIVEBENCH_URL = "https://livebench.ai/"
AA_URL = "https://artificialanalysis.ai/"
CURSORBENCH_URL = "https://cursor.com/cursorbench"

NEAR_MISS_MAX = NEAR_MISS_CANDIDATES

OMITTED_CONSTRUCTS = (
    {
        "blocker_id": "construct-interactive-latency",
        "affected_model": "edition-scope",
        "missing_series": ("interactive_service_responsiveness",),
        "required_identity": "exact Max or documented composite plus 8+ same-extract anchors",
        "sources_investigated": (
            "Epoch zip members with public latency or time-horizon columns",
            "AA reviewed five-row facts",
        ),
        "urls_investigated": (EPOCH_ZIP_URL, AA_URL),
        "reason": (
            "No frozen public series has all five exact Max identities and an 8+ same-extract "
            "anchor panel for interactive service latency"
        ),
        "resolving_evidence": (
            "A frozen same-harness latency extract with all five pilots plus 8+ anchors"
        ),
    },
    {
        "blocker_id": "construct-billed-economics",
        "affected_model": "edition-scope",
        "missing_series": ("provider_billing_record",),
        "required_identity": "verified deployment plus admissible billing record",
        "sources_investigated": (
            "Official five-card lab tariffs",
            "DeepSWE LiteLLM dollars",
            "AA calculated cost columns",
            "CursorBench table averages",
            "Epoch ARC cost-per-task metadata",
        ),
        "urls_investigated": (DEEPSWE_LEDGER_URL, AA_URL, CURSORBENCH_URL, EPOCH_HUB_URL),
        "reason": (
            "No frozen all-five 8+ billed ledger exists. Source-reported WeirdML cost is Access "
            "Economics, not observed provider billing"
        ),
        "resolving_evidence": (
            "An admissible all-five billed task ledger with exact deployment identity"
        ),
    },
    {
        "blocker_id": "construct-hierarchical-bootstrap",
        "affected_model": "edition-scope",
        "missing_series": ("attempt_level_residuals",),
        "required_identity": "attempt-level residuals on the scored extracts",
        "sources_investigated": (
            "Epoch configuration-level means in the frozen zip",
            "DeepSWE official trial ledger (facts-and-citations only)",
        ),
        "urls_investigated": (EPOCH_ZIP_URL, DEEPSWE_LEDGER_URL),
        "reason": (
            "Frozen extracts are configuration-level means without attempt residuals, so "
            "hierarchical bootstrap remains unpublished"
        ),
        "resolving_evidence": (
            "Redistributable attempt-level residuals for every headline series"
        ),
    },
)


class PublicEvidenceBlocker(ConfigModel):
    blocker_id: str
    affected_model: str
    missing_series: tuple[str, ...]
    required_identity: str
    sources_investigated: tuple[str, ...]
    urls_investigated: tuple[str, ...]
    reason: str
    resolving_evidence: str
    umi_public: float | None = None
    present_series: dict[str, str] = Field(default_factory=dict)
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def reject_invented_scores(self) -> PublicEvidenceBlocker:
        if self.umi_public is not None:
            raise ValueError("blocker report must not invent umi_public")
        if not self.missing_series:
            raise ValueError("blocker requires at least one missing series")
        return self


class PublicBlockerReport(ConfigModel):
    report_version: str
    edition_id: str
    status: str
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    headline_published: bool
    unpublished_entity_ids: tuple[str, ...]
    blockers: tuple[PublicEvidenceBlocker, ...]

    @model_validator(mode="after")
    def reject_scored_blockers(self) -> PublicBlockerReport:
        scored = [item.blocker_id for item in self.blockers if item.umi_public is not None]
        if scored:
            raise ValueError("blocker rows must not carry invented scores")
        return self


def _config_blocker(
    *,
    blocker_id: str,
    candidate: dict[str, Any],
    urls: tuple[str, ...],
    sources: tuple[str, ...],
    extra_notes: tuple[str, ...] = (),
) -> dict[str, Any]:
    present = _present_series(candidate["config_ids"])
    required = [
        spec["id"] for spec in public_series_specs(load_public_edition_config(edition="v0.5"))
    ]
    missing = tuple(series_id for series_id in required if series_id not in present)
    notes = list(extra_notes)
    return {
        "blocker_id": blocker_id,
        "affected_model": candidate["candidate_id"],
        "missing_series": missing,
        "required_identity": (
            f"exact {candidate['requested_effort']} configuration on all ten common-core series"
        ),
        "sources_investigated": sources,
        "urls_investigated": urls,
        "reason": (
            "Frozen Epoch extract is missing required common-core series for this exact identity"
        ),
        "resolving_evidence": (
            "Same-zip rows for every missing series at the exact config/effort identity, "
            "including a high-effort WeirdML cost suffix if Access is required"
        ),
        "umi_public": None,
        "present_series": present,
        "notes": tuple(notes),
    }


def _scope_blocker(raw: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    missing = raw["missing_series"]
    if isinstance(missing, str):
        missing = (missing,)
    payload = {
        "blocker_id": extra["blocker_id"] if extra else f"series-{missing[0]}",
        "affected_model": raw["affected_model"],
        "missing_series": tuple(missing),
        "required_identity": raw["required_identity"],
        "sources_investigated": tuple(raw["sources_investigated"]),
        "urls_investigated": extra["urls_investigated"] if extra else (EPOCH_ZIP_URL, DEEPSWE_URL),
        "reason": raw["reason"],
        "resolving_evidence": raw["resolving_evidence"],
        "umi_public": None,
        "present_series": extra.get("present_series", {}) if extra else {},
        "notes": extra.get("notes", ()) if extra else (),
    }
    return payload


def build_blocker_report() -> dict[str, Any]:
    verify_epoch_zip()
    audits = {item["candidate_id"]: item for item in audit_named_candidates()["candidates"]}
    blockers: list[dict[str, Any]] = []
    grok = CANDIDATES[0]
    gemini = CANDIDATES[1]
    blockers.append(
        _config_blocker(
            blocker_id="candidate-grok-4.5-high",
            candidate=grok,
            urls=(EPOCH_ZIP_URL, WEIRDML_URL, EPOCH_HUB_URL),
            sources=(
                "Epoch weirdml_external.csv",
                "Epoch remaining common-core members",
                "WeirdML public leaderboard citation",
            ),
            extra_notes=tuple(audits["grok-4.5-high"]["notes"]),
        )
    )
    blockers.append(
        _config_blocker(
            blocker_id="candidate-gemini-3.1-pro-preview",
            candidate=gemini,
            urls=(EPOCH_ZIP_URL, WEIRDML_URL, EPOCH_HUB_URL),
            sources=(
                "Epoch weirdml_external.csv including unsuffixed Cost per run=1.36",
                "gemini-3.1-pro-preview_high (incomplete suffix row)",
                "WeirdML public leaderboard citation",
            ),
            extra_notes=tuple(audits["gemini-3.1-pro-preview"]["notes"]),
        )
    )
    for item in NEAR_MISS_MAX:
        blockers.append(
            _config_blocker(
                blocker_id=f"near-miss-{item['candidate_id']}",
                candidate=item,
                urls=(EPOCH_ZIP_URL, WEIRDML_URL),
                sources=("Epoch common-core members", "Epoch weirdml_external.csv"),
            )
        )
    diagnostic = {item["missing_series"]: item for item in _diagnostic_blockers()}
    blockers.append(
        _scope_blocker(
            diagnostic["deepswe-mean-cost"],
            {
                "blocker_id": "series-deepswe-mean-cost",
                "urls_investigated": (DEEPSWE_URL, DEEPSWE_LEDGER_URL, EPOCH_ZIP_URL),
                "notes": (
                    "Official DeepSWE v1.1 observes Fable cost on 432 of 436 scored attempts",
                ),
            },
        )
    )
    blockers.append(
        _scope_blocker(
            diagnostic["context_reliability_and_factual_discipline"],
            {
                "blocker_id": "construct-context-reliability",
                "urls_investigated": (EPOCH_ZIP_URL, EPOCH_HUB_URL, AA_URL),
                "notes": (
                    "simpleqa_verified.csv has claude-fable-5_xhigh, not claude-fable-5_max",
                ),
            },
        )
    )
    blockers.append(
        _scope_blocker(
            diagnostic["language_data_and_instruction_following"],
            {
                "blocker_id": "construct-language-instruction",
                "urls_investigated": (EPOCH_ZIP_URL, LIVEBENCH_URL, AA_URL),
                "notes": (
                    "live_bench_external.csv has zero 2026 Max pilots; AA extracts are n=5",
                ),
            },
        )
    )
    blockers.extend(OMITTED_CONSTRUCTS)
    unpublished = tuple(
        item["affected_model"]
        for item in blockers
        if item["affected_model"] != "edition-scope"
    )
    report = {
        "report_version": BLOCKER_REPORT_VERSION,
        "edition_id": GOVERNED_EDITION_ID,
        "status": "published_with_documented_blockers",
        "source_artifact_sha256": EPOCH_SHA256,
        "headline_published": True,
        "unpublished_entity_ids": unpublished,
        "blockers": blockers,
    }
    return PublicBlockerReport.model_validate(report).model_dump(mode="json")


def render_blocker_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UMI Public v0.5 evidence blocker report",
        "",
        "This report documents evidence that is genuinely unavailable in the frozen public",
        "archive. It does not invent scores, impute missing cells, or lower gates.",
        "",
        f"Edition: `{report['edition_id']}`. Zip SHA-256: `{report['source_artifact_sha256']}`.",
        f"Status: `{report['status']}`. Governed partial values remain published for "
        "complete common-core rows; no Overall headline is published.",
        "",
        "| Blocker | Affected | Missing series | Why it fails | What would resolve it |",
        "|---|---|---|---|---|",
    ]
    for item in report["blockers"]:
        missing = ", ".join(f"`{series}`" for series in item["missing_series"])
        lines.append(
            f"| `{item['blocker_id']}` | `{item['affected_model']}` | {missing} | "
            f"{item['reason']} | {item['resolving_evidence']} |"
        )
    lines.extend(
        [
            "",
            "Every blocker has `umi_public: null`. Named candidates and `_max` near-misses stay",
            "off the headline. Access keeps the high-effort suffix panel; unsuffixed WeirdML",
            "cost is not admitted.",
            "",
        ]
    )
    for item in report["blockers"]:
        lines.extend(
            [
                f"## {item['blocker_id']}",
                "",
                f"- affected model: `{item['affected_model']}`",
                f"- required identity: {item['required_identity']}",
                f"- missing series: {', '.join(item['missing_series'])}",
                f"- sources investigated: {'; '.join(item['sources_investigated'])}",
                f"- URLs investigated: {'; '.join(item['urls_investigated'])}",
                f"- reason: {item['reason']}",
                f"- resolving evidence: {item['resolving_evidence']}",
                "- umi_public: null",
                "",
            ]
        )
    return "\n".join(lines)


def write_blocker_report(output_dir: Path | None = None) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / "v0.5" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    report = build_blocker_report()
    (destination / "blocker-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = render_blocker_markdown(report)
    (destination / "blocker-report.md").write_text(markdown, encoding="utf-8")
    if output_dir is None:
        docs = ROOT / "docs" / "editions" / "v0.5" / "BLOCKER_REPORT.md"
        docs.parent.mkdir(parents=True, exist_ok=True)
        docs.write_text(markdown, encoding="utf-8")
    return report
