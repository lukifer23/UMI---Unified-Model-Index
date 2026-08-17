"""Headline-readiness audits for named Public candidates. Does not invent scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from umi.edition import GOVERNED_EDITION_ID, ConfigModel, load_public_edition_config
from umi.public import ROOT, epoch_points, load_epoch_member, public_series_specs
from umi.public_certificate import EPOCH_SHA256, verify_epoch_zip

CANDIDATE_CERTIFICATE_VERSION = "umi-public-candidate-certificate-v0.5"
CANDIDATES = (
    {
        "candidate_id": "grok-4.5-high",
        "named_release": "Grok 4.5",
        "requested_effort": "high",
        "config_ids": ("grok-4.5_high",),
    },
    {
        "candidate_id": "gemini-3.1-pro-preview",
        "named_release": "Gemini 3.1 Pro Preview",
        "requested_effort": "high",
        "config_ids": ("gemini-3.1-pro-preview", "gemini-3.1-pro-preview_high"),
    },
)
NEAR_MISS_CANDIDATES = (
    {
        "candidate_id": "gpt-5.6-terra-max",
        "named_release": "GPT-5.6 Terra",
        "requested_effort": "max",
        "config_ids": ("gpt-5.6-terra_max",),
    },
    {
        "candidate_id": "gpt-5.6-luna-max",
        "named_release": "GPT-5.6 Luna",
        "requested_effort": "max",
        "config_ids": ("gpt-5.6-luna_max",),
    },
    {
        "candidate_id": "claude-sonnet-5-max",
        "named_release": "Claude Sonnet 5",
        "requested_effort": "max",
        "config_ids": ("claude-sonnet-5_max",),
    },
    {
        "candidate_id": "claude-opus-4-8-max",
        "named_release": "Claude Opus 4.8",
        "requested_effort": "max",
        "config_ids": ("claude-opus-4-8_max",),
    },
)


class PublicCandidateAudit(ConfigModel):
    certificate_version: str
    candidate_id: str
    named_release: str
    requested_effort: str
    config_ids: tuple[str, ...]
    headline_eligible: bool
    status: str
    present_series: dict[str, str]
    missing_series: tuple[str, ...]
    notes: tuple[str, ...]
    umi_public: float | None = None
    publication_label: str

    @model_validator(mode="after")
    def reject_invented_or_inconsistent_scores(self) -> PublicCandidateAudit:
        if self.umi_public is not None:
            raise ValueError("candidate audit must not invent umi_public")
        if self.missing_series:
            if self.headline_eligible:
                raise ValueError("missing series cannot be headline eligible")
            if self.status != "insufficient_common_support":
                raise ValueError("incomplete candidates must abstain")
        return self


class PublicCandidateAuditReport(ConfigModel):
    certificate_version: str
    edition_id: str
    gate: str
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidates: tuple[PublicCandidateAudit, ...]
    headline_additions: tuple[str, ...]

    @model_validator(mode="after")
    def reject_unearned_headline_additions(self) -> PublicCandidateAuditReport:
        eligible = tuple(item.candidate_id for item in self.candidates if item.headline_eligible)
        if self.headline_additions != eligible:
            raise ValueError("headline_additions must match eligible candidates")
        return self


def _present_series(config_ids: tuple[str, ...]) -> dict[str, str]:
    edition = load_public_edition_config(edition="v0.5")
    found: dict[str, str] = {}
    for spec in public_series_specs(edition):
        points = epoch_points(
            spec["member"],
            spec["field"],
            require_harness=spec.get("harness"),
            panel_filter=spec.get("panel_filter"),
            high_effort_suffixes=edition.normalization.high_effort_suffixes,
        )
        match = next((item for item in points if item.config_id in config_ids), None)
        if match is not None:
            found[spec["id"]] = match.config_id
    return found


def _weirdml_cost_note(config_ids: tuple[str, ...]) -> str | None:
    for row in load_epoch_member("weirdml_external.csv"):
        if row.get("Model version") not in config_ids:
            continue
        cost = row.get("Cost per run")
        if cost:
            return (
                f"{row['Model version']} has WeirdML Cost per run={cost} but is excluded "
                "from the Access high-effort suffix panel"
            )
    return None


def audit_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    present = _present_series(candidate["config_ids"])
    required = [
        spec["id"]
        for spec in public_series_specs(load_public_edition_config(edition="v0.5"))
    ]
    missing = tuple(series_id for series_id in required if series_id not in present)
    notes: list[str] = []
    cost_note = _weirdml_cost_note(candidate["config_ids"])
    if cost_note:
        notes.append(cost_note)
    ready = not missing
    audit = {
        "certificate_version": CANDIDATE_CERTIFICATE_VERSION,
        "candidate_id": candidate["candidate_id"],
        "named_release": candidate["named_release"],
        "requested_effort": candidate["requested_effort"],
        "config_ids": candidate["config_ids"],
        "headline_eligible": ready,
        "status": "published" if ready else "insufficient_common_support",
        "present_series": present,
        "missing_series": missing,
        "notes": tuple(notes),
        "umi_public": None,
        "publication_label": (
            "headline eligible under the v0.5 common core"
            if ready
            else "diagnostic candidate certificate — missing required common-core series"
        ),
    }
    return PublicCandidateAudit.model_validate(audit).model_dump(mode="json")


def audit_named_candidates() -> dict[str, Any]:
    audits = [audit_candidate(item) for item in CANDIDATES]
    report = {
        "certificate_version": CANDIDATE_CERTIFICATE_VERSION,
        "edition_id": GOVERNED_EDITION_ID,
        "gate": "complete ten-series common core plus high-effort Access suffix panel",
        "source_artifact_sha256": verify_epoch_zip(),
        "candidates": audits,
        "headline_additions": tuple(
            item["candidate_id"] for item in audits if item["headline_eligible"]
        ),
    }
    return PublicCandidateAuditReport.model_validate(report).model_dump(mode="json")


def audit_near_miss_candidates() -> tuple[dict[str, Any], ...]:
    return tuple(audit_candidate(item) for item in NEAR_MISS_CANDIDATES)


def write_candidate_audits(output_dir: Path | None = None) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / "v0.5" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    payload = audit_named_candidates()
    if payload["source_artifact_sha256"] != EPOCH_SHA256:
        raise ValueError("candidate audit zip checksum does not match the registry")
    (destination / "candidate-audits.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for item in (*payload["candidates"], *audit_near_miss_candidates()):
        path = destination / f"candidate-{item['candidate_id']}.json"
        path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
