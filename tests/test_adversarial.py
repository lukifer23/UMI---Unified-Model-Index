from __future__ import annotations

from datetime import date

import pytest

from analysis.value_sensitivity import analyze_value_sensitivity
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.scoring import score_dataset
from umi.validation import validate_dataset


def test_sparse_workload_cannot_masquerade_as_broad_headline(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    sparse = synthetic_dataset.model_copy(
        update={
            "efficiency": tuple(
                item
                for item in synthetic_dataset.efficiency
                if item.model_id != "synthetic-alpha" or item.workload == "synthetic-agent-task"
            )
        }
    )
    results = {item.model_id: item for item in score_dataset(sparse, config)}
    alpha = results["synthetic-alpha"]
    beta = results["synthetic-beta"]
    assert alpha.efficiency.score is not None
    assert alpha.coverage.efficiency_workloads_represented == 1
    assert alpha.coverage.efficiency_workload_weighted == pytest.approx(0.20)
    assert alpha.headline_overall is None
    assert beta.coverage.efficiency_workloads_represented == 6
    assert beta.headline_overall is not None


def test_capability_only_is_never_serialized_as_headline(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    capability_only = synthetic_dataset.model_copy(update={"efficiency": (), "pricing": ()})
    result = score_dataset(capability_only, config)[0]
    assert result.partial_overall_estimate == result.capability.score
    assert result.headline_overall is None
    assert not result.eligible
    assert "overall" not in result.model_dump(mode="json")


def test_snapshot_collision_is_rejected(synthetic_dataset: Dataset, config: ProjectConfig) -> None:
    model = synthetic_dataset.models[0].model_copy(update={"snapshot_id": "alpha-snapshot-a"})
    measurement = synthetic_dataset.benchmarks[0].model_copy(
        update={"model_snapshot_id": "alpha-snapshot-b"}
    )
    dataset = synthetic_dataset.model_copy(
        update={
            "models": (model, *synthetic_dataset.models[1:]),
            "benchmarks": (measurement, *synthetic_dataset.benchmarks[1:]),
        }
    )
    assert any(
        "snapshot does not match" in error for error in validate_dataset(dataset, config).errors
    )


def test_harness_mismatch_creates_singleton_cohorts_not_false_comparison(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    models = synthetic_dataset.models[:2]
    records = []
    for index, model in enumerate(models):
        source = next(
            item
            for item in synthetic_dataset.benchmarks
            if item.model_id == model.id and item.benchmark_id == "synthetic-general"
        )
        records.append(source.model_copy(update={"cohort_key": f"incompatible-{index}"}))
    dataset = synthetic_dataset.model_copy(
        update={"models": models, "benchmarks": tuple(records), "efficiency": (), "pricing": ()}
    )
    from umi.validation import DataValidationError

    with pytest.raises(DataValidationError, match="multiple scoring cohorts"):
        score_dataset(dataset, config)


def test_one_percent_and_zero_success_are_stable_and_explicit(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    efficiency = tuple(
        item.model_copy(update={"success_rate": 0.01})
        if item.model_id == "synthetic-delta"
        else item.model_copy(update={"success_rate": 0.0})
        if item.model_id == "synthetic-epsilon"
        else item
        for item in synthetic_dataset.efficiency
    )
    results = {
        item.model_id: item
        for item in score_dataset(
            synthetic_dataset.model_copy(update={"efficiency": efficiency}), config
        )
    }
    assert results["synthetic-delta"].economics.score is not None
    assert results["synthetic-epsilon"].economics.score == 0.0
    # Every attempt-level resource is success-adjusted; fast failure earns no credit.
    assert results["synthetic-epsilon"].efficiency.score is not None
    assert results["synthetic-epsilon"].efficiency.score == 0.0


def test_single_evaluator_caps_high_confidence_and_value_is_sensitive(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    results = score_dataset(synthetic_dataset, config)
    assert all(item.confidence.value != "high" for item in results)
    assert all(item.coverage.source_organization_count == 1 for item in results)
    sensitivity = analyze_value_sensitivity(results, config)
    assert len(sensitivity) == len(results)
    assert all(item.rank_min is not None and item.rank_max is not None for item in sensitivity)


def test_release_window_is_a_headline_gate(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    outside = synthetic_dataset.models[0].model_copy(update={"release_date": date(2026, 6, 1)})
    dataset = synthetic_dataset.model_copy(
        update={"models": (outside, *synthetic_dataset.models[1:])}
    )
    result = next(item for item in score_dataset(dataset, config) if item.model_id == outside.id)
    assert result.partial_overall_estimate is not None
    assert result.headline_overall is None
    assert not result.eligible
    assert any("release date" in message for message in result.diagnostics)
