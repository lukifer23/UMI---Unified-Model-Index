"""Independent validation of published UMI Public scores."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from umi.edition import PUBLIC_EDITION_ID, load_public_edition_config
from umi.identity import load_public_identities
from umi.public import (
    ROOT,
    SeriesSpec,
    entity_map_from_identities,
    epoch_points,
    public_series_specs,
    score_public_edition,
)
from umi.public_blockers import build_blocker_report
from umi.public_candidates import audit_named_candidates
from umi.public_certificate import EPOCH_SHA256, verify_epoch_zip
from umi.public_crosswalk import config_id_for_entity

V04_PILOTS = {
    "claude-opus-5-max",
    "claude-fable-5-max",
    "gpt-5.6-sol-max",
    "kimi-k3-max",
    "glm-5.2-max",
}


def _raw_lookup(
    spec: SeriesSpec,
    mapping: dict[str, str],
    *,
    high_effort_suffixes: tuple[str, ...],
) -> dict[str, float]:
    points = epoch_points(
        spec["member"],
        spec["field"],
        require_harness=spec.get("harness"),
        panel_filter=spec.get("panel_filter"),
        entity_map=mapping,
        high_effort_suffixes=high_effort_suffixes,
    )
    return {item.entity_id: item.raw for item in points if item.entity_id is not None}


def validate_public_scores(
    payload: dict[str, Any],
    *,
    edition_name: str = "v0.4",
) -> dict[str, Any]:
    edition = load_public_edition_config(edition=edition_name)
    identities = load_public_identities(edition=edition_name)
    mapping = entity_map_from_identities(identities, edition=edition_name)
    errors: list[str] = []
    try:
        digest = verify_epoch_zip()
        if digest != EPOCH_SHA256:
            errors.append("Epoch zip checksum mismatch")
    except ValueError as error:
        errors.append(str(error))
    if payload.get("edition_id") != edition.edition_id:
        errors.append("payload edition_id does not match loaded policy")
    allowed_states = {
        "published",
        "experimental_point_score",
        "historical_experimental_point_score",
        "provisional_public_score",
        "certified_public_score",
        "source_concentration_failed",
    }
    if payload.get("publication_state") not in allowed_states:
        errors.append("payload publication_state is not a documented public state")
    rebuilt = score_public_edition(edition_name=edition_name)
    rebuilt_models = {item["entity_id"]: item for item in rebuilt["models"]}
    payload_models = {item["entity_id"]: item for item in payload.get("models", [])}
    if set(rebuilt_models) != set(payload_models):
        errors.append("rebuilt entity set does not match payload")
    for entity_id, item in payload_models.items():
        live = rebuilt_models.get(entity_id)
        if live is None:
            continue
        if not math.isclose(live["umi_public"], item["umi_public"], abs_tol=1e-12):
            errors.append(f"{entity_id} rebuilt umi_public drifted")
    by_id = {item["entity_id"]: item for item in payload["models"]}
    expected_ids = {item.entity_id for item in identities}
    if set(by_id) != expected_ids:
        errors.append("payload entities do not match the identity manifest")
    for identity in identities:
        config_id = config_id_for_entity(identity.entity_id, edition=edition_name)
        if mapping.get(config_id) != identity.entity_id:
            errors.append(f"config map failed for {identity.entity_id}")
        item = by_id.get(identity.entity_id)
        if item is None:
            continue
        expected = (
            edition.weights.overall.capability * item["capability"]
            + edition.weights.overall.operational_efficiency * item["operational_efficiency"]
            + edition.weights.overall.access_economics * item["access_economics"]
        )
        if not math.isclose(item["umi_public"], expected, rel_tol=0, abs_tol=1e-9):
            errors.append(f"{identity.entity_id} umi_public is not the weighted sum")
        for spec in public_series_specs(edition):
            group = {
                "capability": "capability_series",
                "operational_efficiency": "operational_series",
                "access_economics": "access_series",
            }[spec["component"]]
            raw_values = _raw_lookup(
                spec,
                mapping,
                high_effort_suffixes=edition.normalization.high_effort_suffixes,
            )
            published_raw = item[group][spec["id"]]["raw"]
            if identity.entity_id not in raw_values:
                errors.append(f"{identity.entity_id} missing zip raw for {spec['id']}")
            elif not math.isclose(published_raw, raw_values[identity.entity_id], abs_tol=1e-12):
                errors.append(f"{identity.entity_id} {spec['id']} raw does not match the zip")
    reproduction: dict[str, Any] = {}
    if edition_name == "v0.5":
        v04_path = ROOT / "data" / "editions" / "v0.4" / "processed" / "model-scores.json"
        v04 = json.loads(v04_path.read_text(encoding="utf-8"))
        v04_models = {item["entity_id"]: item for item in v04["models"]}
        for entity_id in V04_PILOTS:
            left = by_id[entity_id]["umi_public"]
            right = v04_models[entity_id]["umi_public"]
            reproduction[entity_id] = left
            if not math.isfinite(left) or not math.isfinite(right):
                errors.append(f"{entity_id} v0.5 or frozen v0.4 score is non-finite")
        if v04.get("edition_id") != PUBLIC_EDITION_ID:
            errors.append("frozen v0.4 edition_id is unexpected")
        errors.extend(_live_candidate_errors(set(by_id)))
    return {
        "edition_id": edition.edition_id,
        "valid": not errors,
        "errors": tuple(errors),
        "checked_entities": sorted(expected_ids),
        "v04_reproduction": reproduction,
        "scored_data_fingerprint": payload.get("scored_data_fingerprint"),
    }


def _live_candidate_errors(published_ids: set[str]) -> tuple[str, ...]:
    live = audit_named_candidates()
    errors: list[str] = []
    if live["headline_additions"]:
        errors.append("named candidates must not enter the headline without a complete common core")
    for item in live["candidates"]:
        if item["umi_public"] is not None:
            errors.append(f"{item['candidate_id']} invented umi_public")
        if item["headline_eligible"] or item["status"] != "insufficient_common_support":
            errors.append(f"{item['candidate_id']} is not an abstention")
        if item["candidate_id"] in published_ids:
            errors.append(f"{item['candidate_id']} appears in published model-scores")
    return tuple(errors)


def _stored_candidate_errors() -> tuple[str, ...]:
    live = audit_named_candidates()
    errors: list[str] = []
    path = ROOT / "data" / "editions" / "v0.5" / "processed" / "candidate-audits.json"
    if not path.is_file():
        return ("missing candidate-audits.json",)
    stored = json.loads(path.read_text(encoding="utf-8"))
    if stored.get("headline_additions"):
        errors.append("stored candidate headline_additions must be empty")
    if stored.get("source_artifact_sha256") != live["source_artifact_sha256"]:
        errors.append("stored candidate audit zip checksum drifted")
    live_by_id = {item["candidate_id"]: item for item in live["candidates"]}
    stored_by_id = {item["candidate_id"]: item for item in stored.get("candidates", [])}
    if set(stored_by_id) != set(live_by_id):
        errors.append("stored candidate IDs do not match the live audit")
    for candidate_id, item in live_by_id.items():
        committed = stored_by_id.get(candidate_id)
        if committed is None:
            continue
        if committed.get("missing_series") != item["missing_series"]:
            errors.append(f"{candidate_id} stored missing_series drifted")
        if committed.get("umi_public") is not None:
            errors.append(f"{candidate_id} stored umi_public is not null")
    return tuple(errors)


def _stored_blocker_errors() -> tuple[str, ...]:
    live = build_blocker_report()
    path = ROOT / "data" / "editions" / "v0.5" / "processed" / "blocker-report.json"
    if not path.is_file():
        return ("missing blocker-report.json",)
    stored = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if stored.get("source_artifact_sha256") != live["source_artifact_sha256"]:
        errors.append("stored blocker-report zip checksum drifted")
    live_ids = {item["blocker_id"]: item for item in live["blockers"]}
    stored_ids = {item["blocker_id"]: item for item in stored.get("blockers", [])}
    if set(stored_ids) != set(live_ids):
        errors.append("stored blocker IDs do not match the live report")
    for blocker_id, item in live_ids.items():
        committed = stored_ids.get(blocker_id)
        if committed is None:
            continue
        if committed.get("missing_series") != item["missing_series"]:
            errors.append(f"{blocker_id} missing_series drifted")
        if committed.get("umi_public") is not None:
            errors.append(f"{blocker_id} invented umi_public")
    return tuple(errors)


def validate_public_artifacts(
    edition_name: str = "v0.4",
    scores_path: Path | None = None,
) -> dict[str, Any]:
    path = (
        scores_path
        or ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = validate_public_scores(payload, edition_name=edition_name)
    if edition_name != "v0.5":
        return report
    extra = _stored_candidate_errors() + _stored_blocker_errors()
    errors = tuple(report["errors"]) + extra
    return {**report, "valid": not errors, "errors": errors}
