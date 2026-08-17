from __future__ import annotations

from umi.edition import GOVERNED_EDITION_ID, load_public_edition_config
from umi.feasibility import validate_public_edition_feasibility
from umi.identity import load_public_identities
from umi.public import score_public_edition
from umi.public_uncertainty import quantify_public_uncertainty
from umi.public_validate import validate_public_scores

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
    identities = load_public_identities(edition="v0.5")
    assert {item.entity_id for item in identities} == V04_PILOTS | {
        "gemini-3.6-flash-high",
        "gpt-5.4-2026-03-05-xhigh",
    }


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


def payload_score(payload: dict[str, object], entity_id: str) -> float:
    models = payload["models"]
    assert isinstance(models, list)
    match = next(item for item in models if item["entity_id"] == entity_id)
    value = match["umi_public"]
    assert isinstance(value, float)
    return value
