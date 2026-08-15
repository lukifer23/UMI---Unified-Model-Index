import pytest

from analysis.compare import common_capability_comparison
from umi import __version__
from umi.capability import score_capability
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import BenchmarkDefinition
from umi.scoring import score_dataset


def test_public_package_version_matches_release() -> None:
    assert __version__ == "0.3.9"


def test_synthetic_pipeline_is_eligible_traceable_and_cohort_relative(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    results = {item.model_id: item for item in score_dataset(synthetic_dataset, config)}
    assert len(results) == 5
    assert all(item.eligible for item in results.values())
    assert all(item.overall_coverage == pytest.approx(0.8625) for item in results.values())
    assert all(
        item.independent_or_community_evidence_share == 1 for item in results.values()
    )
    assert all(item.config_fingerprint == config.fingerprint for item in results.values())
    assert all(item.formula_version == "umi-methodology-v0.3.9" for item in results.values())
    assert all(item.headline_overall == item.partial_overall_estimate for item in results.values())
    assert (
        results["synthetic-alpha"].capability.score > results["synthetic-epsilon"].capability.score
    )
    assert results["synthetic-epsilon"].economics.score > results["synthetic-alpha"].economics.score


def test_independent_measurement_wins_over_vendor_conflict(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    result = score_capability(synthetic_dataset, config).components["synthetic-epsilon"]
    assert "bm-general-epsilon" in result.source_record_ids
    assert "bm-general-epsilon-vendor" not in result.source_record_ids
    assert any("conflict consolidated" in message for message in result.diagnostics)


def test_zero_success_is_explicit_worst_economics(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    dataset = synthetic_dataset.model_copy(
        update={
            "efficiency": tuple(
                item.model_copy(update={"success_rate": 0.0})
                if item.model_id == "synthetic-epsilon"
                else item
                for item in synthetic_dataset.efficiency
            )
        }
    )
    result = {item.model_id: item for item in score_dataset(dataset, config)}["synthetic-epsilon"]
    assert result.economics.score == 0.0
    assert result.efficiency.score is not None


def test_family_budget_prevents_duplicate_representation_from_adding_coverage(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    source_definition = next(item for item in config.benchmarks if item.id == "synthetic-general")
    duplicate_definition = BenchmarkDefinition.model_validate(
        {
            **source_definition.model_dump(mode="json"),
            "id": "synthetic-general-aggregate",
            "name": "Synthetic aggregate of general",
            "constituents": ["synthetic-general"],
        }
    )
    new_measurements = tuple(
        item.model_copy(
            update={
                "record_id": f"aggregate-{item.model_id}",
                "benchmark_id": duplicate_definition.id,
            }
        )
        for item in synthetic_dataset.benchmarks
        if item.benchmark_id == "synthetic-general" and item.result_type.value == "independent"
    )
    expanded_config = config.model_copy(
        update={"benchmarks": (*config.benchmarks, duplicate_definition)}
    )
    expanded_dataset = synthetic_dataset.model_copy(
        update={"benchmarks": (*synthetic_dataset.benchmarks, *new_measurements)}
    )
    baseline = score_capability(synthetic_dataset, config).components
    expanded = score_capability(expanded_dataset, expanded_config).components
    for model_id in baseline:
        assert expanded[model_id].coverage == baseline[model_id].coverage
        assert expanded[model_id].score == pytest.approx(baseline[model_id].score)


def test_explicit_representation_priority_is_alias_order_invariant(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    source = next(item for item in config.benchmarks if item.id == "synthetic-general")
    canonical = source.model_copy(
        update={"representation_group": "synthetic-general", "selection_priority": 0}
    )
    alias = source.model_copy(
        update={
            "id": "a-synthetic-general-alias",
            "name": "Lexically earlier alias",
            "representation_group": "synthetic-general",
            "selection_priority": 1,
        }
    )
    expanded_config = ProjectConfig.model_validate(
        {
            **config.model_dump(mode="json"),
            "benchmarks": [
                canonical if item.id == source.id else item for item in config.benchmarks
            ]
            + [alias],
        }
    )
    alias_measurements = tuple(
        item.model_copy(
            update={
                "record_id": f"alias-{item.model_id}",
                "benchmark_id": alias.id,
                "value": 0.0,
            }
        )
        for item in synthetic_dataset.benchmarks
        if item.benchmark_id == source.id and item.result_type.value == "independent"
    )
    expanded_dataset = synthetic_dataset.model_copy(
        update={"benchmarks": (*synthetic_dataset.benchmarks, *alias_measurements)}
    )
    baseline = score_capability(synthetic_dataset, config).components
    expanded = score_capability(expanded_dataset, expanded_config).components
    for model_id in baseline:
        assert expanded[model_id].coverage == baseline[model_id].coverage
        assert expanded[model_id].score == pytest.approx(baseline[model_id].score)

    alias_only_epsilon = expanded_dataset.model_copy(
        update={
            "benchmarks": tuple(
                item
                for item in expanded_dataset.benchmarks
                if not (
                    item.model_id == "synthetic-epsilon"
                    and item.benchmark_id == source.id
                )
            )
        }
    )
    comparison = common_capability_comparison(
        alias_only_epsilon,
        expanded_config,
        ("synthetic-alpha", "synthetic-epsilon"),
    )
    assert any(
        item["benchmark_id"] == "synthetic-general"
        and item["canonical_representation_group"] == "synthetic-general"
        for item in comparison["common_benchmark_series"]
    )
    epsilon = next(
        item for item in comparison["scores"] if item["model_id"] == "synthetic-epsilon"
    )
    general = next(
        item
        for item in epsilon["contributions"]
        if item["benchmark_id"] == "synthetic-general"
    )
    assert general["source_record_ids"] == ["alias-synthetic-epsilon"]


def test_small_cohort_scores_are_provisional(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    ids = {"synthetic-alpha", "synthetic-beta"}
    dataset = synthetic_dataset.model_copy(
        update={
            "models": tuple(item for item in synthetic_dataset.models if item.id in ids),
            "benchmarks": tuple(
                item for item in synthetic_dataset.benchmarks if item.model_id in ids
            ),
            "pricing": tuple(item for item in synthetic_dataset.pricing if item.model_id in ids),
            "efficiency": tuple(
                item for item in synthetic_dataset.efficiency if item.model_id in ids
            ),
        }
    )
    assert all(item.provisional for item in score_dataset(dataset, config))
