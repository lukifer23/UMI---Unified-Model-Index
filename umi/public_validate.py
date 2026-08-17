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
    return {
        "edition_id": edition.edition_id,
        "valid": not errors,
        "errors": tuple(errors),
        "checked_entities": sorted(expected_ids),
        "v04_reproduction": reproduction,
        "scored_data_fingerprint": payload.get("scored_data_fingerprint"),
    }


def validate_public_artifacts(
    edition_name: str = "v0.4",
    scores_path: Path | None = None,
) -> dict[str, Any]:
    path = (
        scores_path
        or ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_public_scores(payload, edition_name=edition_name)
