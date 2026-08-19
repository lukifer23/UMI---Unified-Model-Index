from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

import umi.rootcausebench_review as rootcausebench
from umi.rootcausebench_review import (
    TARGET_ROUTES,
    RootCauseBenchReview,
    build_rootcausebench_review,
    validate_rootcausebench_review,
)


def test_rootcausebench_review_validates_the_frozen_complete_final_trial_cohort() -> None:
    review = build_rootcausebench_review()
    assert review["final_trial_row_count"] == 2808
    assert review["full_cohort_model_count"] == 26
    assert review["anchor_cohort_sufficient"] is True
    assert [item["candidate_pilot_id"] for item in review["models"]] == list(TARGET_ROUTES)
    for model in review["models"]:
        assert model["attempts"] == 108
        assert model["task_count"] == 36
        assert model["attempts_per_task"] == 3
        assert model["unique_trial_directories"] == 108
        assert model["final_trial_errors"] == 0
        assert all(item["observation_count"] == 108 for item in model["resource_observations"])
        assert model["pass_rate"] == pytest.approx(model["successful_final_trials"] / 108)


def test_rootcausebench_review_is_never_promoted_to_a_pilot_score() -> None:
    review = build_rootcausebench_review()
    assert review["scoring_disposition"] == "diagnostic_only"
    assert review["headline_eligible"] is False
    assert review["headline_overall"] is None
    assert "missing-provider-billing-reconciliation" in review["blockers"]
    for model in review["models"]:
        assert model["explicit_inference_effort"] is None
        assert model["exact_pilot_configuration_match"] is False
        assert model["efficiency_admitted"] is False
        assert model["economics_admitted"] is False
        assert any("router cost" in item.lower() for item in model["diagnostics"])


def test_rootcausebench_review_rejects_missing_resource_or_invented_headline() -> None:
    review = build_rootcausebench_review()
    missing_resource = deepcopy(review)
    missing_resource["models"][0]["resource_observations"] = []
    with pytest.raises(ValidationError, match="resource"):
        RootCauseBenchReview.model_validate(missing_resource)
    invented_headline = deepcopy(review)
    invented_headline["headline_eligible"] = True
    with pytest.raises(ValidationError, match="must not emit"):
        RootCauseBenchReview.model_validate(invented_headline)


def test_rootcausebench_review_rejects_new_unreviewed_effort_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = rootcausebench._load_config

    def with_effort(path: object) -> tuple[int, int, dict[str, dict[str, object]]]:
        attempts, timeout, agents = original(path)  # type: ignore[arg-type]
        updated = {name: dict(value) for name, value in agents.items()}
        updated[next(iter(TARGET_ROUTES.values()))]["reasoning_effort"] = "max"
        return attempts, timeout, updated

    monkeypatch.setattr(rootcausebench, "_load_config", with_effort)
    with pytest.raises(ValueError, match="review effort binding"):
        build_rootcausebench_review()


def test_committed_rootcausebench_review_matches_the_frozen_artifact() -> None:
    assert validate_rootcausebench_review()["valid"] is True
