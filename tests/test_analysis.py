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
    assert sufficient[0].spearman == pytest.approx(1.0)


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
        {"benchmark_id": "deepswe-v1.1", "cohort_key": "deepswe-v1.1-2026-08-13"}
    ]
    scores = cast(list[dict[str, object]], comparison["scores"])
    assert {item["coverage"] for item in scores} == {0.165}


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
            "cohort_key": "aa-v4.1.1-critpt-70-test-challenges-pass1",
        },
        {"benchmark_id": "deepswe-v1.1", "cohort_key": "deepswe-v1.1-2026-08-13"},
        {
            "benchmark_id": "gpqa-diamond",
            "cohort_key": "epoch-gpqa-diamond-1.0.6-simple-evals",
        },
        {
            "benchmark_id": "scicode",
            "cohort_key": "aa-v4.1.1-scicode-test-288-background-pass1",
        },
    ]
    assert {item["coverage"] for item in scores} == {0.35625}


def test_source_bound_sensitivity_preserves_declared_margin_without_probability_model(
    real_pilot_dataset: Dataset, real_pilot_config: ProjectConfig
) -> None:
    report = source_bound_capability_sensitivity(real_pilot_dataset, real_pilot_config)
    kimi = next(item for item in report if item["model_id"] == "kimi-k3-max")
    assert kimi["source_bound_lower"] == pytest.approx(63.97739833756913)
    assert kimi["source_bound_upper"] == pytest.approx(73.05142649613376)
    assert kimi["uncertainty"]["kind"] == "confidence_interval"
    assert kimi["uncertainty"]["confidence_level"] == 0.95
    assert "not probabilistic" in kimi["method"]
    assert all(item["benchmark_id"] != "gpqa-diamond" for item in report)
