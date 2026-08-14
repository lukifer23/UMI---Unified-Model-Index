from __future__ import annotations

from math import inf, nan

import pytest
from pydantic import ValidationError

from analysis.pareto_metrics import pareto_dimensions
from umi.config import ProjectConfig, ValueConfig
from umi.derived_metrics import consolidate_cost_per_success
from umi.fingerprints import dataset_fingerprint
from umi.loading import Dataset
from umi.schemas import (
    BenchmarkDefinition,
    BenchmarkFamilyDefinition,
    BenchmarkMeasurement,
    RecordStatus,
)
from umi.scoring import score_dataset
from umi.validation import validate_dataset


def test_unready_real_record_is_blocked_and_override_suppresses_headline(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    model_id = "synthetic-alpha"
    real_model = synthetic_dataset.models[0].model_copy(
        update={"synthetic": False, "notes": "unready test record"}
    )
    dataset = synthetic_dataset.model_copy(
        update={"models": (real_model, *synthetic_dataset.models[1:])}
    )
    report = validate_dataset(dataset, config)
    assert report.schema_valid
    assert not report.scoring_ready
    assert any("snapshot" in failure for failure in report.readiness_failures)

    normal = {item.model_id: item for item in score_dataset(dataset, config)}[model_id]
    assert normal.capability.score is None
    assert normal.headline_overall is None

    override = {
        item.model_id: item for item in score_dataset(dataset, config, allow_unready=True)
    }[model_id]
    assert override.partial_overall_estimate is not None
    assert override.headline_overall is None
    assert not override.scoring_ready
    assert override.confidence.value == "low"
    assert any("unready evidence override" in item for item in override.diagnostics)


def test_diagnostic_record_is_retained_but_does_not_change_scored_fingerprint(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    baseline = score_dataset(synthetic_dataset, config)[0]
    diagnostic = synthetic_dataset.benchmarks[0].model_copy(
        update={
            "record_id": "diagnostic-outlier",
            "value": 10_000.0,
            "record_status": RecordStatus.DIAGNOSTIC_ONLY,
        }
    )
    expanded = synthetic_dataset.model_copy(
        update={"benchmarks": (*synthetic_dataset.benchmarks, diagnostic)}
    )
    changed = score_dataset(expanded, config)[0]
    assert changed.capability.score == baseline.capability.score
    assert changed.scored_data_fingerprint == baseline.scored_data_fingerprint
    assert changed.dataset_fingerprint != baseline.dataset_fingerprint


def test_hierarchical_efficiency_coverage_counts_metric_weight(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    efficiency = tuple(
        item.model_copy(
            update={
                "mean_total_tokens": None,
                "mean_turns": None,
                "mean_wall_seconds": None,
                "mean_cost_per_attempt": None,
            }
        )
        if item.model_id == "synthetic-alpha"
        else item
        for item in synthetic_dataset.efficiency
    )
    result = {
        item.model_id: item
        for item in score_dataset(
            synthetic_dataset.model_copy(update={"efficiency": efficiency}), config
        )
    }["synthetic-alpha"]
    assert result.coverage.efficiency_workloads_represented == 6
    assert result.coverage.efficiency_metric_weighted == pytest.approx(0.10)
    assert result.efficiency.coverage == pytest.approx(0.10)
    assert result.headline_overall is None


def test_capability_coverage_counts_missing_representation_budget(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    original = next(item for item in config.benchmarks if item.id == "synthetic-general")
    second = BenchmarkDefinition.model_validate(
        {
            **original.model_dump(mode="json"),
            "id": "synthetic-general-second",
            "name": "Synthetic second general representation",
        }
    )
    expanded = ProjectConfig.model_validate(
        {**config.model_dump(mode="json"), "benchmarks": [*config.benchmarks, second]}
    )
    baseline = score_dataset(synthetic_dataset, config)[0]
    changed = score_dataset(synthetic_dataset, expanded)[0]
    assert changed.capability.coverage < baseline.capability.coverage
    assert changed.coverage.capability_representations_represented == 3
    assert changed.coverage.capability_representations_total == 6


def test_success_adjustment_uses_median_of_paired_record_ratios(
    synthetic_dataset: Dataset,
) -> None:
    source = synthetic_dataset.efficiency[0]
    records = [
        source.model_copy(
            update={"record_id": "ratio-a", "mean_cost_per_attempt": 10.0, "success_rate": 0.5}
        ),
        source.model_copy(
            update={"record_id": "ratio-b", "mean_cost_per_attempt": 100.0, "success_rate": 1.0}
        ),
    ]
    value, selected, conflict = consolidate_cost_per_success(records)
    assert value == pytest.approx(60.0)
    assert value != pytest.approx(55.0 / 0.75)
    assert {item.record_id for item in selected} == {"ratio-a", "ratio-b"}
    assert conflict


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_nonfinite_source_values_are_rejected(
    synthetic_dataset: Dataset, value: float
) -> None:
    raw = synthetic_dataset.benchmarks[0].model_dump(mode="python")
    raw["value"] = value
    with pytest.raises(ValidationError):
        BenchmarkMeasurement.model_validate(raw)


def test_dataset_fingerprint_tracks_values_snapshots_cohorts_and_order(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    baseline = dataset_fingerprint(synthetic_dataset, config)
    reversed_dataset = synthetic_dataset.model_copy(
        update={
            "models": tuple(reversed(synthetic_dataset.models)),
            "benchmarks": tuple(reversed(synthetic_dataset.benchmarks)),
            "efficiency": tuple(reversed(synthetic_dataset.efficiency)),
        }
    )
    assert dataset_fingerprint(reversed_dataset, config) == baseline

    benchmark = synthetic_dataset.benchmarks[0]
    for update in (
        {"value": benchmark.value + 1},
        {"model_snapshot_id": "different-snapshot"},
        {"cohort_key": "different-cohort"},
    ):
        changed_record = benchmark.model_copy(update=update)
        changed = synthetic_dataset.model_copy(
            update={"benchmarks": (changed_record, *synthetic_dataset.benchmarks[1:])}
        )
        assert dataset_fingerprint(changed, config) != baseline


def test_family_weight_above_cap_is_invalid(config: ProjectConfig) -> None:
    family = config.families[0]
    invalid_family = BenchmarkFamilyDefinition.model_validate(
        {**family.model_dump(mode="json"), "weight": 1.0, "cap": 0.5}
    )
    families = [invalid_family, *config.families[1:]]
    with pytest.raises(ValidationError, match="weight exceeds cap"):
        ProjectConfig.model_validate({**config.model_dump(mode="json"), "families": families})


def test_value_scenarios_reject_mathematical_duplicates() -> None:
    with pytest.raises(ValidationError, match="mathematically distinct"):
        ValueConfig.model_validate(
            {
                "baseline": "geometric",
                "scenarios": [
                    {"name": "geometric", "formula": "geometric_mean_v1"},
                    {
                        "name": "weighted-half",
                        "formula": "weighted_geometric_v1",
                        "alpha": 0.5,
                    },
                ],
            }
        )


def test_pareto_results_are_workload_and_cohort_scoped(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    output = pareto_dimensions(synthetic_dataset, score_dataset(synthetic_dataset, config))
    assert output
    assert all(item.metric and item.workload and item.cohort_key for item in output)
    assert {item.workload_category for item in output} >= {
        "coding_agents",
        "research_analysis",
    }
