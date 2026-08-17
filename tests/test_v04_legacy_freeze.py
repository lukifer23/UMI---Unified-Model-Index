from __future__ import annotations

import hashlib
from pathlib import Path

from umi.edition import PUBLIC_EDITION_ID, load_public_edition_config

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


def test_v04_edition_identity_is_frozen() -> None:
    config = load_public_edition_config(edition="v0.4")
    assert config.edition_id == PUBLIC_EDITION_ID
    assert config.formula_version == "umi-methodology-v0.4.0"


def test_frozen_v04_processed_artifacts_are_byte_identical() -> None:
    for relative, expected in GOLDEN.items():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert digest == expected, relative
