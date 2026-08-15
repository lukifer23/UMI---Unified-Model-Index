from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from umi.config import ProjectConfig, load_project_config
from umi.readiness import readiness_failures
from umi.schema_export import rendered_schemas
from umi.schemas import (
    ArtifactCaptureType,
    BenchmarkMeasurement,
    ConfigurationVerification,
    EfficiencyMeasurement,
    IdentityAssurance,
    ModelConfiguration,
    PricingRecord,
    ResultType,
)

ROOT = Path(__file__).parents[1]


def provenance() -> dict[str, object]:
    return {
        "record_id": "synthetic-record",
        "source": {
            "organization": "UMI Test",
            "url": "https://example.invalid/source",
            "accessed": "2026-08-14",
        },
        "result_type": "independent",
        "metric_definition": "SYNTHETIC TEST DATA",
    }


def test_configuration_is_deterministic_and_complete() -> None:
    first = load_project_config(ROOT / "tests" / "fixtures" / "config")
    second = load_project_config(ROOT / "tests" / "fixtures" / "config")
    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64
    assert sum(first.weights.capability_domains.values()) == pytest.approx(1.0)
    assert len(first.weights.sensitivity_sets) == 5
    assert {item.id for item in first.workloads} == {
        "synthetic-agent-task",
        "synthetic-browser",
        "synthetic-coding",
        "synthetic-general-interaction",
        "synthetic-long-horizon",
        "synthetic-research",
    }


def test_workload_hierarchy_and_efficiency_metrics_fail_closed() -> None:
    config = load_project_config(ROOT / "tests" / "fixtures" / "config")
    raw = config.model_dump(mode="python")
    raw["weights"]["efficiency"] = {"made_up_metric": 1.0}
    with pytest.raises(ValidationError, match="unsupported metric"):
        ProjectConfig.model_validate(raw)

    raw = config.model_dump(mode="python")
    raw["workload_families"][0]["weight"] = 0.5
    with pytest.raises(ValidationError, match="family weights.*sum to 1"):
        ProjectConfig.model_validate(raw)


def test_pricing_requires_at_least_one_nonnegative_price() -> None:
    data = {
        **provenance(),
        "model_id": "synthetic-model",
        "effective_date": date(2026, 8, 14),
    }
    with pytest.raises(ValidationError, match="at least one price"):
        PricingRecord.model_validate(data)
    with pytest.raises(ValidationError):
        PricingRecord.model_validate({**data, "input_per_million": -1})


def test_efficiency_rejects_bad_rates_counts_and_empty_observations() -> None:
    data = {
        **provenance(),
        "model_id": "synthetic-model",
        "workload": "synthetic-workload",
        "workload_category": "agentic",
        "attempts": 10,
        "success_rate": 0.5,
    }
    with pytest.raises(ValidationError, match="at least one observation"):
        EfficiencyMeasurement.model_validate(data)
    with pytest.raises(ValidationError):
        EfficiencyMeasurement.model_validate({**data, "attempts": 0, "mean_turns": 1})
    with pytest.raises(ValidationError):
        EfficiencyMeasurement.model_validate({**data, "success_rate": 1.1, "mean_turns": 1})
    with pytest.raises(ValidationError):
        EfficiencyMeasurement.model_validate({**data, "mean_total_tokens": -1})
    with pytest.raises(ValidationError, match="cannot exceed attempts"):
        EfficiencyMeasurement.model_validate(
            {
                **data,
                "successful_attempts": 11,
                "mean_turns": 1,
            }
        )
    with pytest.raises(ValidationError, match="does not reconcile"):
        EfficiencyMeasurement.model_validate(
            {
                **data,
                "successful_attempts": 4,
                "mean_turns": 1,
            }
        )
    with pytest.raises(ValidationError, match="cannot exceed attempts"):
        EfficiencyMeasurement.model_validate(
            {
                **data,
                "mean_turns": 1,
                "observation_counts": {"turns": 11},
            }
        )
    with pytest.raises(ValidationError, match="no corresponding"):
        EfficiencyMeasurement.model_validate(
            {
                **data,
                "mean_turns": 1,
                "observation_counts": {"tool_calls": 10},
            }
        )


def test_real_efficiency_requires_bound_success_and_full_mean_denominators() -> None:
    model = ModelConfiguration.model_validate(
        {
            "id": "resource-model",
            "family": "Resource Model",
            "provider": "UMI Test",
            "release_date": "2026-08-01",
            "configuration": "max",
            "identity_kind": "named_release",
            "identity_assurance": IdentityAssurance.LABEL_EXACT,
            "named_release": "Resource Model",
            "open_weights": False,
        }
    )
    record = EfficiencyMeasurement.model_validate(
        {
            **provenance(),
            "record_id": "resource-record",
            "model_id": model.id,
            "source_model_id": "Resource Model Max",
            "workload": "resource-workload",
            "workload_category": "coding_agents",
            "cohort_key": "resource-cohort",
            "evaluation_date": "2026-08-14",
            "attempts": 10,
            "successful_attempts": 5,
            "success_rate": 0.5,
            "mean_input_tokens": 100,
            "observation_counts": {"input_tokens": 10},
            "benchmark_version": "resource-v1",
            "harness_version": "resource-harness-v1",
            "evaluator": "UMI Test",
            "capture_type": ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
            "source_artifact_id": "resource-artifact",
            "configuration_verification": ConfigurationVerification(
                model_label_exact=True,
                release_label_exact=True,
                effort_label_exact=True,
                fallback_absent=True,
            ),
            "result_type": ResultType.INDEPENDENT,
        }
    )
    assert readiness_failures(record, model) == ()
    assert "successful attempt count is missing" in readiness_failures(
        record.model_copy(update={"successful_attempts": None}), model
    )
    assert "observation count does not match attempts for mean_input_tokens" in (
        readiness_failures(
            record.model_copy(
                update={"observation_counts": record.observation_counts.model_copy(
                    update={"input_tokens": 9}
                )}
            ),
            model,
        )
    )


def test_capability_source_as_of_date_is_not_relabelled_as_evaluation_date() -> None:
    model = ModelConfiguration.model_validate(
        {
            "id": "dated-model",
            "family": "Dated Model",
            "provider": "UMI Test",
            "release_date": "2026-08-01",
            "configuration": "max",
            "identity_kind": "named_release",
            "identity_assurance": IdentityAssurance.LABEL_EXACT,
            "named_release": "Dated Model",
            "open_weights": False,
        }
    )
    record = BenchmarkMeasurement.model_validate(
        {
            **provenance(),
            "record_id": "dated-record",
            "benchmark_id": "dated-benchmark",
            "model_id": model.id,
            "source_model_id": "Dated Model Max",
            "value": 50,
            "cohort_key": "dated-cohort",
            "evaluation_date": None,
            "measurement_as_of_date": "2026-08-14",
            "benchmark_version": "dated-v1",
            "harness_version": "dated-harness-v1",
            "evaluator": "UMI Test",
            "capture_type": ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
            "source_artifact_id": "dated-artifact",
            "configuration_verification": ConfigurationVerification(
                model_label_exact=True,
                release_label_exact=True,
                effort_label_exact=True,
                fallback_absent=True,
            ),
            "result_type": ResultType.INDEPENDENT,
        }
    )
    assert readiness_failures(record, model) == ()
    assert record.evaluation_date is None


def test_unknown_fields_and_units_are_rejected() -> None:
    path = ROOT / "tests" / "fixtures" / "config"
    raw = load_project_config(path).benchmarks[0].model_dump(mode="json")
    raw["unit"] = "requests_per_fortnight"
    from umi.schemas import BenchmarkDefinition

    with pytest.raises(ValidationError):
        BenchmarkDefinition.model_validate(raw)
    with pytest.raises(ValidationError):
        BenchmarkDefinition.model_validate({**raw, "unit": "score", "secret_weight": 4})


def test_committed_json_schemas_match_pydantic_models() -> None:
    for name, rendered in rendered_schemas().items():
        assert (ROOT / "schemas" / name).read_text(encoding="utf-8") == rendered
