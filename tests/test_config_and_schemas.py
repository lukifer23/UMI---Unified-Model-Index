from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from umi.config import load_project_config
from umi.schemas import EfficiencyMeasurement, PricingRecord

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
    first = load_project_config(ROOT / "config")
    second = load_project_config(ROOT / "config")
    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64
    assert sum(first.weights.capability_domains.values()) == pytest.approx(1.0)
    assert len(first.weights.sensitivity_sets) == 5


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


def test_unknown_fields_and_units_are_rejected() -> None:
    path = ROOT / "config"
    raw = load_project_config(path).benchmarks[0].model_dump(mode="json")
    raw["unit"] = "requests_per_fortnight"
    from umi.schemas import BenchmarkDefinition

    with pytest.raises(ValidationError):
        BenchmarkDefinition.model_validate(raw)
    with pytest.raises(ValidationError):
        BenchmarkDefinition.model_validate({**raw, "unit": "score", "secret_weight": 4})
