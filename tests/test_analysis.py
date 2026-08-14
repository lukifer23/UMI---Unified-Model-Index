import pytest

from analysis.correlations import benchmark_correlations
from analysis.pareto import ParetoPoint, pareto_frontier
from analysis.rankings import rank_results
from analysis.sensitivity import analyze_sensitivity
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.scoring import score_dataset


def test_rankings_use_average_tied_ranks(synthetic_dataset: Dataset, config: ProjectConfig) -> None:
    results = score_dataset(synthetic_dataset, config)[:2]
    tied = [item.model_copy(update={"overall": 50.0}) for item in results]
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
