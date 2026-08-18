from __future__ import annotations

import math
from pathlib import Path

import pytest

from umi.public import (
    epoch_points,
    score_public_bundle,
    score_public_edition,
    series_score,
    transform_lower_better,
)
from umi.public_bundle import load_public_scoring_bundle
from umi.public_paths import resolve_epoch_zip
from umi.scoring import score_dataset


def test_score_public_bundle_rejects_raw_payload() -> None:
    with pytest.raises(TypeError, match="PublicScoringBundle"):
        score_public_bundle({"edition_id": "umi-public-v0.5"})


def test_bundle_dir_and_explicit_zip_score_offline(tmp_path: Path) -> None:
    source = resolve_epoch_zip()
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    target = bundle_dir / source.name
    target.write_bytes(source.read_bytes())
    payload = score_public_edition(edition_name="v0.5", bundle_dir=bundle_dir)
    assert payload["certified"] is False
    assert payload["models"]
    again = score_public_bundle(
        load_public_scoring_bundle(edition_name="v0.5", zip_path=target)
    )
    assert again["scored_data_fingerprint"] == payload["scored_data_fingerprint"]


def test_v05_uses_log_cost_transform_not_plus_one() -> None:
    log_score = transform_lower_better(0.1, mode="log")
    legacy = transform_lower_better(0.1, mode="neglog1p")
    assert log_score == pytest.approx(-math.log(0.1))
    assert legacy == pytest.approx(-math.log(1.1))
    assert log_score != legacy


def test_v05_rejects_out_of_range_proportion() -> None:
    with pytest.raises(ValueError, match="outside"):
        series_score(
            1.2,
            (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
            kind="proportion",
            reject_out_of_range=True,
        )


def test_declared_duplicate_conflict_fails() -> None:
    with pytest.raises(ValueError, match="conflicting"):
        epoch_points(
            "weirdml_external.csv",
            "Accuracy",
            duplicate_policy="declared",
            excluded_config_ids=(),
        )


def test_v05_excludes_conflicting_weirdml_row() -> None:
    points = epoch_points(
        "weirdml_external.csv",
        "Accuracy",
        duplicate_policy="declared",
        excluded_config_ids=("Qwen3-235B-A22B-Thinking-2507",),
    )
    assert all(item.config_id != "Qwen3-235B-A22B-Thinking-2507" for item in points)
    assert {item.source_row_id for item in points if item.source_row_id}


def test_v04_keeps_first_seen_and_legacy_transform() -> None:
    v04 = score_public_edition(edition_name="v0.4")
    by_id = {item["entity_id"]: item["umi_public"] for item in v04["models"]}
    assert by_id["gpt-5.6-sol-max"] == pytest.approx(66.26583886547628, abs=1e-12)


def test_anchor_members_are_fingerprinted() -> None:
    from umi.edition import load_public_edition_config
    from umi.public_scale import build_public_panels_and_scales

    edition = load_public_edition_config(edition="v0.5")
    bundle = load_public_scoring_bundle(edition_name="v0.5")
    panels, scales = build_public_panels_and_scales(bundle, edition)
    assert all(item.members for item in panels)
    assert all(item.panel_fingerprint for item in panels)
    again, again_scales = build_public_panels_and_scales(bundle, edition)
    assert [item.panel_fingerprint for item in again] == [
        item.panel_fingerprint for item in panels
    ]
    assert [item.scale_id for item in again_scales] == [item.scale_id for item in scales]


def test_score_dataset_allows_labeled_synthetic(synthetic_dataset, config) -> None:
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score_dataset(synthetic_dataset, config, synthetic=True)
    assert not [item for item in caught if issubclass(item.category, DeprecationWarning)]
