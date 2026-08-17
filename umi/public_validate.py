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
    SERIES,
    SeriesSpec,
    config_id_for_entity,
    entity_map_from_identities,
    epoch_points,
    score_public_edition,
)
from umi.public_candidates import audit_named_candidates
from umi.public_certificate import EPOCH_SHA256, verify_epoch_zip

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
) -> dict[str, float]:
    points = epoch_points(
        spec["member"],
        spec["field"],
        require_harness=spec.get("harness"),
        panel_filter=spec.get("panel_filter"),
        entity_map=mapping,
    )
    return {item.entity_id: item.raw for item in points if item.entity_id is not None}


def validate_public_scores(
    payload: dict[str, Any],
    *,
    edition_name: str = "v0.4",
) -> dict[str, Any]:
    edition = load_public_edition_config(edition=edition_name)
    identities = load_public_identities(edition=edition_name)
    mapping = entity_map_from_identities(identities)
    errors: list[str] = []
    try:
        digest = verify_epoch_zip()
        if digest != EPOCH_SHA256:
            errors.append("Epoch zip checksum mismatch")
    except ValueError as error:
        errors.append(str(error))
    if payload.get("edition_id") != edition.edition_id:
        errors.append("payload edition_id does not match loaded policy")
    if payload.get("publication_state") != "published":
        errors.append("payload is not published")
    rebuilt = score_public_edition(edition_name=edition_name)
    if rebuilt["scored_data_fingerprint"] != payload.get("scored_data_fingerprint"):
        errors.append("rebuilt scored_data_fingerprint does not match payload")
    by_id = {item["entity_id"]: item for item in payload["models"]}
    expected_ids = {item.entity_id for item in identities}
    if set(by_id) != expected_ids:
        errors.append("payload entities do not match the identity manifest")
    for identity in identities:
        config_id = config_id_for_entity(identity.entity_id)
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
        for spec in SERIES:
            group = {
                "capability": "capability_series",
                "operational_efficiency": "operational_series",
                "access_economics": "access_series",
            }[spec["component"]]
            raw_values = _raw_lookup(spec, mapping)
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
            if not math.isclose(left, right, abs_tol=1e-12):
                errors.append(f"{entity_id} v0.5 score drifted from frozen v0.4")
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
    extra = _stored_candidate_errors()
    errors = tuple(report["errors"]) + extra
    return {**report, "valid": not errors, "errors": errors}
