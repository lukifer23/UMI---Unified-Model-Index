from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import BenchmarkDefinition
from umi.validation import DataValidationError, validate_dataset


def test_fixture_is_valid_but_preserves_conflict_warning(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    report = validate_dataset(synthetic_dataset, config)
    assert report.valid
    assert any("conflicting benchmark" in warning for warning in report.warnings)


def test_duplicate_record_ids_are_errors(synthetic_dataset: Dataset, config: ProjectConfig) -> None:
    duplicate = synthetic_dataset.benchmarks[0].model_copy(update={"model_id": "synthetic-beta"})
    dataset = synthetic_dataset.model_copy(
        update={"benchmarks": (*synthetic_dataset.benchmarks, duplicate)}
    )
    report = validate_dataset(dataset, config)
    assert not report.valid
    assert any("duplicate record id" in error for error in report.errors)
    try:
        report.raise_for_errors()
    except DataValidationError as error:
        assert error.errors == report.errors
    else:
        raise AssertionError("raise_for_errors did not raise")


def test_unknown_model_and_benchmark_are_errors(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    unknown_model = synthetic_dataset.efficiency[0].model_copy(
        update={"record_id": "unknown-model-record", "model_id": "absent-model"}
    )
    unknown_benchmark = synthetic_dataset.benchmarks[0].model_copy(
        update={"record_id": "unknown-benchmark-record", "benchmark_id": "absent-benchmark"}
    )
    dataset = synthetic_dataset.model_copy(
        update={
            "efficiency": (*synthetic_dataset.efficiency, unknown_model),
            "benchmarks": (*synthetic_dataset.benchmarks, unknown_benchmark),
        }
    )
    errors = validate_dataset(dataset, config).errors
    assert any("unknown model" in error for error in errors)
    assert any("unknown benchmark" in error for error in errors)


def test_declared_overlap_must_share_family(
    synthetic_dataset: Dataset, config: ProjectConfig
) -> None:
    original = config.benchmarks[0]
    invalid_overlap = BenchmarkDefinition.model_validate(
        {
            **original.model_dump(mode="json"),
            "id": "invalid-overlap",
            "family": "different-family",
            "constituents": [original.id],
        }
    )
    invalid_config = config.model_copy(update={"benchmarks": (*config.benchmarks, invalid_overlap)})
    errors = validate_dataset(synthetic_dataset, invalid_config).errors
    assert any("must share a family" in error for error in errors)
