from __future__ import annotations

import pytest

from analysis.public_dashboard import build_public_dashboard, write_public_dashboard
from umi.public import score_public_edition


def test_dashboard_reads_published_scores_and_does_not_invent_intervals() -> None:
    payload = score_public_edition()
    dashboard = build_public_dashboard(payload)
    by_id = {item["entity_id"]: item for item in payload["models"]}
    assert dashboard["scored_data_fingerprint"] == payload["scored_data_fingerprint"]
    assert dashboard["publication_state"] == "published"
    for row in dashboard["ranking"]:
        source = by_id[row["entity_id"]]
        assert row["umi_public"] == pytest.approx(source["umi_public"], abs=1e-6)
        assert row["capability"] == pytest.approx(source["capability"], abs=1e-6)
        assert row["interval"] is None
        assert row["interval_status"] == "unpublished_point_extracts"
        reconstructed = (
            row["capability_weighted"]
            + row["operational_efficiency_weighted"]
            + row["access_economics_weighted"]
        )
        assert reconstructed == pytest.approx(row["umi_public"], abs=1e-5)


def test_dashboard_refuses_to_plot_a_null_public_score() -> None:
    payload = score_public_edition()
    payload["models"][0]["umi_public"] = None
    with pytest.raises(ValueError, match="null umi_public"):
        build_public_dashboard(payload)
    payload["publication_state"] = "insufficient_common_support"
    with pytest.raises(ValueError, match="published umi_public"):
        build_public_dashboard(payload)


def test_dashboard_artifacts_are_deterministic(tmp_path) -> None:
    payload = score_public_edition()
    first = write_public_dashboard(payload, tmp_path / "a")
    second = write_public_dashboard(payload, tmp_path / "b")
    assert first == second
    html = (tmp_path / "a" / "public-dashboard.html").read_text(encoding="utf-8")
    assert payload["scored_data_fingerprint"] in html
    assert "provider bill" in html
    assert html.count("unpublished") >= 5
    ranking = (tmp_path / "a" / "public-ranking.csv").read_text(encoding="utf-8")
    assert "umi_public" in ranking
    assert "gpt-5.6-sol-max" in ranking
