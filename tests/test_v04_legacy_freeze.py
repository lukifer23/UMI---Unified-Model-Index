from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from umi.edition import (
    EXPERIMENTAL_POINT_SCORE,
    PUBLIC_EDITION_ID,
    load_public_edition_config,
)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = {
    "data/editions/v0.4/processed/model-scores.json": (
        "6a58f83f6328b169e877e3863bddd3901ede012b8103e180145a008a46af2e5a"
    ),
    "data/editions/v0.4/processed/common-core.json": (
        "c2ae227dc774600d4cfc506d90105fcbd77bff0fb95ac47bbc1010166117f883"
    ),
    "data/editions/v0.4/processed/rejected-evidence.json": (
        "e0c4ee08df54e46d5ec3fb87c9b726e6e97adf3f8b5ea01d90a2a3f9b7c3b7a2"
    ),
}
V04_FINGERPRINT = "e266af13b966cf79cfc5086513ec35f60cf2194f896f41f4b332f60ac9788e6d"
V04_SCORES = {
    "gpt-5.6-sol-max": 66.26583886547628,
    "kimi-k3-max": 59.69066272741414,
    "claude-opus-5-max": 55.510021169743936,
    "claude-fable-5-max": 54.429636426057556,
    "glm-5.2-max": 54.202702676964044,
}


def test_v04_edition_identity_is_frozen() -> None:
    config = load_public_edition_config(edition="v0.4")
    assert config.edition_id == PUBLIC_EDITION_ID
    assert config.formula_version == "umi-methodology-v0.4.0"
    assert config.release_class == EXPERIMENTAL_POINT_SCORE


def test_frozen_v04_processed_artifacts_are_byte_identical() -> None:
    for relative, expected in GOLDEN.items():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert digest == expected, relative


def test_v04_cannot_be_relabeled_as_governed() -> None:
    config = load_public_edition_config(edition="v0.4")
    payload = config.model_dump(mode="json")
    payload["release_class"] = "governed_public_index"
    with pytest.raises(ValidationError, match="historical_experimental_point_score"):
        type(config).model_validate(payload)


def test_v04_is_the_experimental_five_model_point_score() -> None:
    payload = json.loads(
        (ROOT / "data" / "editions" / "v0.4" / "processed" / "model-scores.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["edition_id"] == PUBLIC_EDITION_ID
    assert payload["scored_data_fingerprint"] == V04_FINGERPRINT
    assert payload["publication_state"] == "published"
    assert "certificate" not in payload
    assert "uncertainty" not in payload
    by_id = {item["entity_id"]: item for item in payload["models"]}
    assert set(by_id) == set(V04_SCORES)
    for entity_id, expected in V04_SCORES.items():
        assert by_id[entity_id]["umi_public"] == expected
