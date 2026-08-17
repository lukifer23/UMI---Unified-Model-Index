from __future__ import annotations

import math

import pytest

from umi.edition import load_public_edition_config
from umi.feasibility import validate_public_edition_feasibility
from umi.public import (
    SERIES,
    deepswe_points,
    epoch_points,
    score_public_edition,
    series_score,
    write_public_artifacts,
)

REQUIRED_ENTITIES = {
    "claude-opus-5-max",
    "claude-fable-5-max",
    "gpt-5.6-sol-max",
    "kimi-k3-max",
    "glm-5.2-max",
}


def test_deepswe_anchor_panel_has_at_least_eight_configs() -> None:
    points = deepswe_points("Pass@1")
    assert len(points) >= 8
    pilots = {item.entity_id for item in points if item.entity_id}
    assert pilots == REQUIRED_ENTITIES


def test_every_required_series_covers_all_five_pilots() -> None:
    for spec in SERIES:
        points = epoch_points(
            spec["member"],
            spec["field"],
            require_harness=spec.get("harness"),
            panel_filter=spec.get("panel_filter"),
        )
        pilots = {item.entity_id for item in points if item.entity_id}
        assert pilots == REQUIRED_ENTITIES, spec["id"]
        assert len(points) >= 8, spec["id"]


def test_public_scores_are_published_finite_and_display_invariant() -> None:
    first = score_public_edition()
    second = score_public_edition()
    assert first == second
    assert first["publication_state"] == "published"
    assert first["required_common_core_coverage"] == 1.0
    assert first["scored_data_fingerprint"]
    assert first["scored_data_fingerprint"] == second["scored_data_fingerprint"]
    by_id = {item["entity_id"]: item for item in first["models"]}
    assert set(by_id) == REQUIRED_ENTITIES
    ranks = {item["rank"] for item in first["models"]}
    assert ranks == {1, 2, 3, 4, 5}
    for item in first["models"]:
        assert item["publication_state"] == "published"
        assert item["umi_public"] is not None
        assert item["access_economics"] is not None
        for key in ("capability", "operational_efficiency", "access_economics", "umi_public"):
            assert math.isfinite(item[key])
            assert 0 < item[key] < 100
        expected = (
            0.55 * item["capability"]
            + 0.25 * item["operational_efficiency"]
            + 0.20 * item["access_economics"]
        )
        assert item["umi_public"] == pytest.approx(expected)
        assert set(item["capability_series"]) == {
            spec["id"] for spec in SERIES if spec["component"] == "capability"
        }
    opus = by_id["claude-opus-5-max"]
    glm = by_id["glm-5.2-max"]
    assert opus["capability"] > glm["capability"]
    access_scores = {item["entity_id"]: item["access_economics"] for item in first["models"]}
    assert access_scores["glm-5.2-max"] > access_scores["kimi-k3-max"]
    assert access_scores["kimi-k3-max"] > access_scores["claude-opus-5-max"]
    assert access_scores["claude-opus-5-max"] > access_scores["claude-fable-5-max"]
    ordered = sorted(first["models"], key=lambda item: item["rank"])
    assert ordered[0]["umi_public"] >= ordered[-1]["umi_public"]


def test_fable_incomplete_cost_is_excluded_from_complete_series() -> None:
    complete = deepswe_points("Mean cost (USD)", require_complete_cost=True)
    assert "claude-fable-5-max" not in {item.entity_id for item in complete}
    assert "claude-opus-5-max" in {item.entity_id for item in complete}
    payload = score_public_edition()
    assert "deepswe-mean-cost" not in payload["series"]
    reasons = " ".join(str(item["reason"]) for item in payload["blockers"])
    assert "432 of 436" in reasons


def test_non_finite_epoch_values_are_rejected() -> None:
    points = epoch_points("chess_puzzles.csv", "mean_score")
    assert all(math.isfinite(item.raw) for item in points)


def test_hiding_a_display_row_does_not_change_pilot_scores() -> None:
    points = deepswe_points("Pass@1")
    panel = tuple(item.raw for item in points)
    opus = next(item for item in points if item.entity_id == "claude-opus-5-max")
    full = series_score(opus.raw, panel, kind="proportion")
    hidden = series_score(opus.raw, panel[1:] + panel[:1], kind="proportion")
    assert full["score"] == hidden["score"]


def test_public_policy_stays_statically_feasible() -> None:
    config = load_public_edition_config()
    validate_public_edition_feasibility(config)
    assert set(item.value for item in config.weights.capability_domains) == {
        "general_reasoning_and_knowledge",
        "software_engineering",
        "agentic_and_tool_mediated_work",
        "mathematics_and_science",
    }
    assert list(config.weights.access_economics)[0].value == "public_benchmark_task_cost"
    assert config.eligibility.maximum_source_share == pytest.approx(0.35)


def test_weight_change_changes_public_fingerprint() -> None:
    baseline = score_public_edition()
    config = load_public_edition_config()
    payload = config.model_dump(mode="json")
    payload["weights"]["overall"]["capability"] = 0.56
    payload["weights"]["overall"]["operational_efficiency"] = 0.24
    mutated = type(config).model_validate(payload)
    changed = score_public_edition(mutated)
    assert changed["scored_data_fingerprint"] != baseline["scored_data_fingerprint"]
    assert {item["entity_id"] for item in changed["models"]} == REQUIRED_ENTITIES


def test_write_public_artifacts_round_trips(tmp_path) -> None:
    payload = write_public_artifacts(tmp_path)
    assert (tmp_path / "model-scores.json").is_file()
    assert (tmp_path / "rejected-evidence.json").is_file()
    assert (tmp_path / "common-core.json").is_file()
    assert payload["publication_state"] == "published"
    assert all(item["umi_public"] is not None for item in payload["models"])
