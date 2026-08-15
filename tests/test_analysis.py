from typing import cast

import pytest

from analysis.compare import common_capability_comparison
from analysis.correlations import benchmark_correlations
from analysis.pareto import ParetoPoint, pareto_frontier
from analysis.rankings import rank_results
from analysis.sensitivity import analyze_sensitivity
from analysis.uncertainty import source_bound_capability_sensitivity
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.scoring import score_dataset


def test_rankings_use_average_tied_ranks(synthetic_dataset: Dataset, config: ProjectConfig) -> None:
    results = score_dataset(synthetic_dataset, config)[:2]
    tied = [item.model_copy(update={"headline_overall": 50.0}) for item in results]
    assert [item.rank for item in rank_results(tied)] == [1.5, 1.5]


def test_sensitivity_runs_every_weight_set(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    output = analyze_sensitivity(score_dataset(synthetic_dataset, config), config)
    assert len(output) == 5
    assert all(item.rank_min is not None and item.rank_max is not None for item in output)
    assert all(item.stability is not None and 0 <= item.stability <= 1 for item in output)


def test_correlations_report_overlap_and_gate_interpretation(
    synthetic_dataset: Dataset,
) -> None:
    sufficient = benchmark_correlations(synthetic_dataset, minimum_overlap=5)
    insufficient = benchmark_correlations(synthetic_dataset, minimum_overlap=6)
    assert len(sufficient) == 3
    assert all(item.overlap == 5 and item.interpretable for item in sufficient)
    assert all(not item.interpretable for item in insufficient)
    assert all(
        item.pearson is None
        and item.spearman is None
        and item.interpretability_reason == "insufficient_overlap"
        for item in insufficient
    )
    assert sufficient[0].spearman == pytest.approx(1.0)

    constant = synthetic_dataset.model_copy(
        update={
            "benchmarks": tuple(
                item.model_copy(update={"value": 1.0})
                if item.benchmark_id == "synthetic-general"
                else item
                for item in synthetic_dataset.benchmarks
            )
        }
    )
    constant_results = benchmark_correlations(constant, minimum_overlap=5)
    affected = [
        item
        for item in constant_results
        if "synthetic-general" in {item.benchmark_a, item.benchmark_b}
    ]
    assert affected
    assert all(
        item.pearson is None
        and item.spearman is None
        and item.interpretability_reason == "constant_series"
        for item in affected
    )


def test_pareto_dominance_and_equal_points() -> None:
    output = {
        item.model_id: item
        for item in pareto_frontier(
            [
                ParetoPoint("a", capability=90, expense=5),
                ParetoPoint("b", capability=80, expense=6),
                ParetoPoint("c", capability=90, expense=5),
                ParetoPoint("d", capability=70, expense=3),
            ]
        )
    }
    assert output["b"].dominated
    assert output["b"].dominator_ids == ("a", "c")
    assert not output["a"].dominated
    assert not output["c"].dominated
    assert not output["d"].dominated


def test_common_evidence_comparison_excludes_model_specific_support(
    real_pilot_dataset: Dataset, real_pilot_config: ProjectConfig
) -> None:
    comparison = common_capability_comparison(
        real_pilot_dataset,
        real_pilot_config,
        (
            "claude-opus-5-max",
            "claude-fable-5-max",
            "gpt-5.6-sol-max",
            "kimi-k3-max",
            "glm-5.2-max",
        ),
    )
    assert comparison["common_benchmark_series"] == [
        {
            "benchmark_id": "deepswe-v1.1",
            "canonical_representation_group": "deepswe-v1.1",
            "cohort_key": "deepswe-v1.1-2026-08-13",
        }
    ]
    scores = cast(list[dict[str, object]], comparison["scores"])
    assert {item["coverage"] for item in scores} == {0.0825}


def test_three_model_common_evidence_excludes_unready_arena_support(
    real_pilot_dataset: Dataset, real_pilot_config: ProjectConfig
) -> None:
    comparison = common_capability_comparison(
        real_pilot_dataset,
        real_pilot_config,
        ("claude-opus-5-max", "kimi-k3-max", "glm-5.2-max"),
    )
    series = cast(list[dict[str, str]], comparison["common_benchmark_series"])
    scores = cast(list[dict[str, object]], comparison["scores"])
    assert series == [
        {
            "benchmark_id": "critpt",
            "canonical_representation_group": "critpt",
            "cohort_key": "aa-v4.1.1-critpt-70-test-challenges-pass1",
        },
        {
            "benchmark_id": "cursorbench-3.2",
            "canonical_representation_group": "cursorbench-3.2",
            "cohort_key": "cursorbench-3.2-public-leaderboard-2026-08-14",
        },
        {
            "benchmark_id": "deepswe-v1.1",
            "canonical_representation_group": "deepswe-v1.1",
            "cohort_key": "deepswe-v1.1-2026-08-13",
        },
        {
            "benchmark_id": "gdpval-aa-v2",
            "canonical_representation_group": "gdpval-aa-v2",
            "cohort_key": "aa-gdpval-v2-public-leaderboard-2026-08-15",
        },
        {
            "benchmark_id": "gpqa-diamond",
            "canonical_representation_group": "gpqa-diamond",
            "cohort_key": "epoch-gpqa-diamond-1.0.6-simple-evals",
        },
        {
            "benchmark_id": "hle",
            "canonical_representation_group": "hle",
            "cohort_key": "aa-hle-v4.1-may-2025-text-2158-pass1-gpt4o-judge",
        },
        {
            "benchmark_id": "scicode",
            "canonical_representation_group": "scicode",
            "cohort_key": "aa-v4.1.1-scicode-test-288-background-pass1",
        },
        {
            "benchmark_id": "tau3-banking",
            "canonical_representation_group": "tau3-banking",
            "cohort_key": "aa-tau3-banking-97-tasks-5-repeats-bm25-grep-2026-08-15",
        },
    ]
    assert {item["coverage"] for item in scores} == {0.6937500000000001}

    five_model = common_capability_comparison(
        real_pilot_dataset,
        real_pilot_config,
        (
            "claude-opus-5-max",
            "claude-fable-5-max",
            "gpt-5.6-sol-max",
            "kimi-k3-max",
            "glm-5.2-max",
        ),
    )
    five_kimi = next(
        item for item in cast(list[dict[str, object]], five_model["scores"])
        if item["model_id"] == "kimi-k3-max"
    )
    three_kimi = next(item for item in scores if item["model_id"] == "kimi-k3-max")
    five_deepswe = next(
        item
        for item in cast(list[dict[str, object]], five_kimi["contributions"])
        if item["benchmark_id"] == "deepswe-v1.1"
    )
    three_deepswe = next(
        item
        for item in cast(list[dict[str, object]], three_kimi["contributions"])
        if item["benchmark_id"] == "deepswe-v1.1"
    )
    assert five_deepswe["normalized_value"] == three_deepswe["normalized_value"] == 25.0
    assert five_deepswe["normalization_panel_id"] == three_deepswe["normalization_panel_id"]
    deep_panel = next(
        item
        for item in cast(list[dict[str, object]], comparison["normalization_panels"])
        if item["benchmark_id"] == "deepswe-v1.1"
    )
    gpqa_panel = next(
        item
        for item in cast(list[dict[str, object]], comparison["normalization_panels"])
        if item["benchmark_id"] == "gpqa-diamond"
    )
    hle_panel = next(
        item
        for item in cast(list[dict[str, object]], comparison["normalization_panels"])
        if item["benchmark_id"] == "hle"
    )
    assert len(cast(list[str], deep_panel["model_ids"])) == 5
    assert len(cast(list[str], gpqa_panel["model_ids"])) == 4
    assert len(cast(list[str], hle_panel["model_ids"])) == 4
    assert deep_panel["requested_strategy"] == "robust_z"
    assert deep_panel["applied_strategy"] == "percentile"
    assert cast(dict[str, object], deep_panel["normalization_trace"])[
        "fallback_reason"
    ] == "below_minimum_robust_cohort"
    reordered = real_pilot_dataset.model_copy(
        update={"benchmarks": tuple(reversed(real_pilot_dataset.benchmarks))}
    )
    reordered_comparison = common_capability_comparison(
        reordered,
        real_pilot_config,
        ("claude-opus-5-max", "kimi-k3-max", "glm-5.2-max"),
    )
    assert reordered_comparison["score_scale"] == comparison["score_scale"]
    assert reordered_comparison["normalization_panels"] == comparison[
        "normalization_panels"
    ]
    intervals = cast(list[dict[str, object]], comparison["sensitivity_intervals"])
    assert len(intervals) == 9
    assert sum(item["interval_origin"] == "derived_from_standard_error" for item in intervals) == 3
    assert all(
        item["assumption"] == "normal_approximation" and item["z_value"] == 1.96
        for item in intervals
        if item["interval_origin"] == "derived_from_standard_error"
    )
    robustness = {
        item["model_id"]: cast(dict[str, object], item["rank_robustness"])
        for item in scores
    }
    assert all(item["scenario_count"] == 512 and item["exhaustive"] for item in robustness.values())
    assert robustness["glm-5.2-max"]["possible_ranks"] == [3.0]
    assert robustness["claude-opus-5-max"]["possible_ranks"] == [1.0]
    assert "glm-5.2-max" in robustness["kimi-k3-max"]["robustly_dominates"]
    assert "probability" not in str(comparison).lower()


def test_source_bound_sensitivity_preserves_declared_margin_without_probability_model(
    real_pilot_dataset: Dataset, real_pilot_config: ProjectConfig
) -> None:
    report = source_bound_capability_sensitivity(real_pilot_dataset, real_pilot_config)
    kimi = next(
        item
        for item in report
        if item["model_id"] == "kimi-k3-max"
        and item["benchmark_id"] == "deepswe-v1.1"
    )
    assert kimi["source_bound_lower"] == pytest.approx(63.97739833756913)
    assert kimi["source_bound_upper"] == pytest.approx(73.05142649613376)
    assert kimi["uncertainty"]["kind"] == "confidence_interval"
    assert kimi["uncertainty"]["confidence_level"] == 0.95
    assert "not probabilistic" in kimi["method"]
    assert all(item["benchmark_id"] != "gpqa-diamond" for item in report)
