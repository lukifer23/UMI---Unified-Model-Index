from __future__ import annotations

import hashlib
from pathlib import Path

from umi.edition import LEGACY_EDITION_ID
from umi.version import (
    ENGINE_VERSION,
    FORMULA_VERSION,
    NORMALIZATION_VERSION,
    PACKAGE_VERSION,
)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = {
    "data/pilots/v0.3/processed/comparison-certificate-three-model.json": (
        "2a790575e37ecaaeeb3a5d9fd8b98453bdac7e911f0cec9a7d4be6d33c830f10"
    ),
    "data/pilots/v0.3/processed/model-specific-partial-estimates.json": (
        "094db06a5da2f3a70cb6bcc79b19b89670aea82b194c52c4ae78f4584441b496"
    ),
    "data/pilots/v0.3/processed/common-evidence-three-model-comparison.json": (
        "6e08fa2a78eb5ea0f07f1063c7779ffdcf5a5101d2d7b23ad327a71db404b001"
    ),
    "data/pilots/v0.3/processed/common-evidence-five-model-comparison.json": (
        "dc491e4bed73d5e5b2dbbc3b96f973ee3524b87912c9e731f27c74b59a7be73b"
    ),
    "data/pilots/v0.3/raw/audit.yaml": (
        "c2f196976753957b30f53fd26ef3553222e2c1e61736d55d557d079db33ba0de"
    ),
}


def test_legacy_edition_identity_and_formula_are_unchanged() -> None:
    assert LEGACY_EDITION_ID == "umi-public-v0.3-legacy"
    assert PACKAGE_VERSION == "0.5.0"
    assert FORMULA_VERSION == "umi-methodology-v0.3.15"
    assert NORMALIZATION_VERSION == "umi-normalization-v0.3.4"
    assert ENGINE_VERSION == "umi-engine-v0.3.13"


def test_frozen_v03_processed_artifacts_are_byte_identical() -> None:
    for relative, expected in GOLDEN.items():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert digest == expected, relative
