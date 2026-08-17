from __future__ import annotations

from umi.public import deepswe_points, score_public_edition, series_score


def test_deepswe_anchor_panel_has_at_least_eight_configs() -> None:
    points = deepswe_points("Pass@1")
    assert len(points) >= 8
    pilots = {item.entity_id for item in points if item.entity_id}
    assert pilots == {
        "claude-opus-5-max",
        "claude-fable-5-max",
        "gpt-5.6-sol-max",
        "kimi-k3-max",
        "glm-5.2-max",
    }


def test_public_scores_are_finite_and_display_invariant() -> None:
    first = score_public_edition()
    second = score_public_edition()
    assert first == second
    assert first["publication_state"] == "insufficient_common_support"
    by_id = {item["entity_id"]: item for item in first["models"]}
    assert set(by_id) == {
        "claude-opus-5-max",
        "claude-fable-5-max",
        "gpt-5.6-sol-max",
        "kimi-k3-max",
        "glm-5.2-max",
    }
    for item in first["models"]:
        assert item["umi_public"] is None
        assert item["capability"] is not None
        assert 0 < item["capability"] < 100
        assert item["operational_efficiency"] is not None
        assert item["access_economics"] is None
    opus = by_id["claude-opus-5-max"]["capability"]
    glm = by_id["glm-5.2-max"]["capability"]
    assert opus > glm


def test_fable_incomplete_cost_is_excluded_from_complete_series() -> None:
    complete = deepswe_points("Mean cost (USD)", require_complete_cost=True)
    assert "claude-fable-5-max" not in {item.entity_id for item in complete}
    assert "claude-opus-5-max" in {item.entity_id for item in complete}


def test_hiding_a_display_row_does_not_change_pilot_scores() -> None:
    points = deepswe_points("Pass@1")
    panel = tuple(item.raw for item in points)
    opus = next(item for item in points if item.entity_id == "claude-opus-5-max")
    full = series_score(opus.raw, panel, kind="proportion")
    hidden = series_score(opus.raw, panel[1:] + panel[:1], kind="proportion")
    assert full["score"] == hidden["score"]
