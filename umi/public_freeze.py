"""Frozen expanded Public evidence and unpublished-candidate audits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from umi.edition import GOVERNED_EDITION_ID, ConfigModel
from umi.public import ROOT
from umi.public_bundle import load_public_scoring_bundle
from umi.public_candidates import (
    PublicCandidateAudit,
    audit_named_candidates,
    audit_near_miss_candidates,
)
from umi.public_certificate import EPOCH_SHA256, verify_epoch_zip

FREEZE_VERSION = "umi-public-evidence-freeze-v0.5"
FROZEN_SCORED_DATA_FINGERPRINT = (
    "5624c3b417e4c0e42dd35411065f200c38ccfc6b49474f47cb671c2d43a22c6c"
)
FROZEN_EVIDENCE_FINGERPRINT = (
    "bc636b728785fc81183173a4b14092d2c1fcb704189275a20c8cde896a3fc687"
)
EXPANDED_ENTITY_IDS = (
    "claude-opus-5-max",
    "claude-fable-5-max",
    "gpt-5.6-sol-max",
    "kimi-k3-max",
    "glm-5.2-max",
    "gemini-3.6-flash-high",
    "gpt-5.4-2026-03-05-xhigh",
)
FROZEN_SCORES = {
    "gpt-5.6-sol-max": 66.26583886547628,
    "kimi-k3-max": 59.69066272741414,
    "gpt-5.4-2026-03-05-xhigh": 55.51137725670947,
    "claude-opus-5-max": 55.510021169743936,
    "gemini-3.6-flash-high": 55.4399971625043,
    "claude-fable-5-max": 54.429636426057556,
    "glm-5.2-max": 54.202702676964044,
}
NAMED_CANDIDATE_IDS = ("grok-4.5-high", "gemini-3.1-pro-preview")
NEAR_MISS_IDS = (
    "gpt-5.6-terra-max",
    "gpt-5.6-luna-max",
    "claude-sonnet-5-max",
    "claude-opus-4-8-max",
)


class PublicAcceptedScore(ConfigModel):
    entity_id: str
    umi_public: float
    rank: int


class PublicEvidenceFreeze(ConfigModel):
    freeze_version: str
    status: str
    edition_id: str
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    scored_data_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_entity_ids: tuple[str, ...]
    accepted_scores: tuple[PublicAcceptedScore, ...]
    series: tuple[str, ...]
    named_candidates: tuple[PublicCandidateAudit, ...]
    near_miss_candidates: tuple[PublicCandidateAudit, ...]
    headline_additions: tuple[str, ...]
    limitations: tuple[str, ...]
    freeze_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def reject_drift_or_invented_scores(self) -> PublicEvidenceFreeze:
        if self.status != "frozen_expanded_public_evidence":
            raise ValueError("evidence freeze status must be frozen_expanded_public_evidence")
        if self.edition_id != GOVERNED_EDITION_ID:
            raise ValueError("evidence freeze belongs to umi-public-v0.5")
        if self.source_artifact_sha256 != EPOCH_SHA256:
            raise ValueError("evidence freeze zip checksum does not match the registry")
        if self.evidence_fingerprint != FROZEN_EVIDENCE_FINGERPRINT:
            raise ValueError("expanded evidence_fingerprint drifted")
        if self.scored_data_fingerprint != FROZEN_SCORED_DATA_FINGERPRINT:
            raise ValueError("expanded scored_data_fingerprint drifted")
        if set(self.accepted_entity_ids) != set(EXPANDED_ENTITY_IDS):
            raise ValueError("accepted entity set is not the frozen expanded cohort")
        if self.headline_additions:
            raise ValueError("evidence freeze must not add unpublished candidates")
        by_id = {item.entity_id: item for item in self.accepted_scores}
        if set(by_id) != set(FROZEN_SCORES):
            raise ValueError("accepted scores do not match the frozen expanded cohort")
        for entity_id, expected in FROZEN_SCORES.items():
            if abs(by_id[entity_id].umi_public - expected) > 1e-12:
                raise ValueError(f"{entity_id} frozen umi_public drifted")
        unpublished = (*self.named_candidates, *self.near_miss_candidates)
        seen = [item.candidate_id for item in unpublished]
        if len(seen) != len(set(seen)):
            raise ValueError("unpublished candidate IDs must be unique")
        if {item.candidate_id for item in self.named_candidates} != set(NAMED_CANDIDATE_IDS):
            raise ValueError("named candidate set drifted")
        if {item.candidate_id for item in self.near_miss_candidates} != set(NEAR_MISS_IDS):
            raise ValueError("near-miss candidate set drifted")
        for item in unpublished:
            if item.umi_public is not None:
                raise ValueError(f"{item.candidate_id} invented umi_public")
            if item.candidate_id in self.accepted_entity_ids:
                raise ValueError(f"{item.candidate_id} cannot be both accepted and unpublished")
            if item.headline_eligible or item.status != "insufficient_common_support":
                raise ValueError(f"{item.candidate_id} is not an abstention")
        return self


def _digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def build_evidence_freeze(
    payload: dict[str, Any] | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    if edition_name != "v0.5":
        raise ValueError("expanded evidence freeze is a v0.5 surface")
    scores = payload or json.loads(
        (ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json").read_text(
            encoding="utf-8"
        )
    )
    bundle = load_public_scoring_bundle(edition_name=edition_name)
    named = audit_named_candidates()
    near_miss = audit_near_miss_candidates()
    accepted = [
        {
            "entity_id": item["entity_id"],
            "umi_public": item["umi_public"],
            "rank": item["rank"],
        }
        for item in sorted(scores["models"], key=lambda row: row["rank"])
    ]
    unsigned = {
        "freeze_version": FREEZE_VERSION,
        "status": "frozen_expanded_public_evidence",
        "edition_id": GOVERNED_EDITION_ID,
        "source_artifact_sha256": verify_epoch_zip(),
        "evidence_fingerprint": bundle.evidence_fingerprint,
        "scored_data_fingerprint": scores["scored_data_fingerprint"],
        "accepted_entity_ids": list(bundle.entity_ids),
        "accepted_scores": accepted,
        "series": list(scores["series"]),
        "named_candidates": named["candidates"],
        "near_miss_candidates": list(near_miss),
        "headline_additions": list(named["headline_additions"]),
        "limitations": (
            "This freeze binds the seven complete common-core identities and the unpublished "
            "candidate audits. It does not invent umi_public for incomplete identities.",
            "Grok 4.5 High and Gemini 3.1 Pro Preview remain diagnostic abstentions.",
            "Four _max near-misses miss WeirdML and stay unpublished.",
        ),
    }
    report = {**unsigned, "freeze_fingerprint": _digest(unsigned)}
    return PublicEvidenceFreeze.model_validate(report).model_dump(mode="json")


def write_evidence_freeze(
    payload: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    report = build_evidence_freeze(payload, edition_name=edition_name)
    (destination / "evidence-freeze.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
