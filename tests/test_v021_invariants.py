from __future__ import annotations

from math import inf, nan

import pytest
from pydantic import ValidationError

from analysis.correlations import benchmark_correlations
from analysis.pareto_metrics import pareto_dimensions
from analysis.sensitivity import analyze_sensitivity
from umi.config import ProjectConfig, SensitivityWeights, ValueConfig
from umi.derived_metrics import consolidate_cost_per_success
from umi.fingerprints import dataset_fingerprint
from umi.loading import Dataset
from umi.schemas import (
    BenchmarkDefinition,
    BenchmarkFamilyDefinition,
    BenchmarkMeasurement,
    CostBasis,
    Direction,
    RecordStatus,
    TaskEconomicsMeasurement,
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


def test_headline_requires_efficiency_even_with_direct_economics(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    source = synthetic_dataset.efficiency[0]
    economics = tuple(
        TaskEconomicsMeasurement.model_validate(
            {
                **source.model_dump(mode="python", exclude={
                    "attempts",
                    "success_rate",
                    "mean_input_tokens",
                    "mean_output_tokens",
                    "mean_reasoning_tokens",
                    "mean_cached_tokens",
                    "mean_total_tokens",
                    "mean_turns",
                    "mean_wall_seconds",
                    "mean_tool_calls",
                        "mean_cost_per_attempt",
                        "observed_output_tokens_summary",
                        "observed_agent_steps_summary",
                        "observed_cost_summary_usd",
                }),
                "record_id": f"direct-economics-{model.id}",
                "model_id": model.id,
                "cost_basis": CostBasis.SUCCESSFUL_TASK,
                "mean_cost_usd": float(index + 1),
                "evaluation_date": "2026-08-14",
                "model_snapshot_id": "unspecified",
            }
        )
        for index, model in enumerate(synthetic_dataset.models)
    )
    dataset = synthetic_dataset.model_copy(
        update={"efficiency": (), "task_economics": economics}
    )
    results = score_dataset(dataset, config)
    assert all(item.capability.score is not None for item in results)
    assert all(item.efficiency.score is None for item in results)
    assert all(item.economics.score is not None for item in results)
    assert all(item.headline_overall is None for item in results)


def test_sensitivity_recomputes_eligibility_per_scenario(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    result = score_dataset(synthetic_dataset, config)[0]
    result = result.model_copy(
        update={
            "capability": result.capability.model_copy(update={"coverage": 0.60}),
            "efficiency": result.efficiency.model_copy(update={"coverage": 0.50}),
            "economics": result.economics.model_copy(update={"coverage": 0.40}),
            "eligible": False,
            "headline_overall": None,
        }
    )
    scenarios = (
        SensitivityWeights(name="baseline", capability=0.55, efficiency=0.25, economics=0.20),
        SensitivityWeights(
            name="capability-heavy", capability=0.90, efficiency=0.05, economics=0.05
        ),
    )
    custom = config.model_copy(
        update={
            "weights": config.weights.model_copy(update={"sensitivity_sets": scenarios}),
            "eligibility": config.eligibility.model_copy(
                update={"minimum_overall_coverage": 0.55}
            ),
        }
    )
    sensitivity = analyze_sensitivity([result], custom)[0]
    assert not sensitivity.baseline_eligible
    assert sensitivity.eligible_scenario_count == 1
    assert sensitivity.ineligible_scenario_count == 1
    assert sensitivity.eligibility_changed


def test_correlations_align_metric_direction_and_exclude_diagnostics(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    lower_definition = next(
        item for item in config.benchmarks if item.id == "synthetic-code"
    ).model_copy(update={"direction": Direction.LOWER})
    changed_definitions = tuple(
        lower_definition if item.id == lower_definition.id else item
        for item in config.benchmarks
    )
    changed_config = config.model_copy(update={"benchmarks": changed_definitions})
    diagnostic = synthetic_dataset.benchmarks[0].model_copy(
        update={
            "record_id": "diagnostic-other-cohort",
            "cohort_key": "diagnostic-cohort",
            "record_status": RecordStatus.DIAGNOSTIC_ONLY,
        }
    )
    dataset = synthetic_dataset.model_copy(
        update={"benchmarks": (*synthetic_dataset.benchmarks, diagnostic)}
    )
    output = benchmark_correlations(dataset, minimum_overlap=5, config=changed_config)
    pair = next(
        item
        for item in output
        if {item.benchmark_a, item.benchmark_b} == {"synthetic-general", "synthetic-code"}
    )
    assert pair.spearman == pytest.approx(-1.0)
    assert all(item.cohort_a != "diagnostic-cohort" for item in output)


def test_default_normalization_strategy_affects_efficiency_scores(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    robust = score_dataset(synthetic_dataset, config)[0].efficiency.score
    percentile_config = config.model_copy(
        update={
            "normalization": config.normalization.model_copy(
                update={"default_strategy": "percentile"}
            )
        }
    )
    percentile = score_dataset(synthetic_dataset, percentile_config)[0].efficiency.score
    assert robust != percentile
