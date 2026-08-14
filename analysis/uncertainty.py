from __future__ import annotations

from umi.capability import score_capability
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.readiness import scoring_dataset
from umi.schemas import BenchmarkMeasurement, MeasurementUncertainty


def _bounds(value: float, uncertainty: MeasurementUncertainty) -> tuple[float, float] | None:
    if uncertainty.lower is not None and uncertainty.upper is not None:
        return uncertainty.lower, uncertainty.upper
    if uncertainty.margin is not None:
        return value - uncertainty.margin, value + uncertainty.margin
    return None


def source_bound_capability_sensitivity(
    dataset: Dataset, config: ProjectConfig
) -> list[dict[str, object]]:
    """Re-score one source-declared benchmark bound at a time, without a probability model."""
    scored, _ = scoring_dataset(dataset)
    output: list[dict[str, object]] = []
    for record in sorted(scored.benchmarks, key=lambda item: item.record_id):
        if not isinstance(record, BenchmarkMeasurement) or record.uncertainty is None:
            continue
        bounds = _bounds(record.value, record.uncertainty)
        if bounds is None:
            continue
        lower, upper = bounds
        if lower > upper:
            continue
        component = score_capability(scored, config).components[record.model_id]
        extremes: dict[str, float | None] = {}
        for name, value in (("lower", lower), ("upper", upper)):
            modified = scored.model_copy(
                update={
                    "benchmarks": tuple(
                        item.model_copy(update={"value": value})
                        if item.record_id == record.record_id
                        else item
                        for item in scored.benchmarks
                    )
                }
            )
            extremes[name] = score_capability(modified, config).components[record.model_id].score
        output.append(
            {
                "model_id": record.model_id,
                "record_id": record.record_id,
                "benchmark_id": record.benchmark_id,
                "cohort_key": record.cohort_key,
                "central_value": record.value,
                "source_bound_lower": lower,
                "source_bound_upper": upper,
                "uncertainty": record.uncertainty.model_dump(mode="json"),
                "central_capability": component.score,
                "capability_when_record_at_lower_bound": extremes["lower"],
                "capability_when_record_at_upper_bound": extremes["upper"],
                "method": (
                    "one-record-at-a-time source-bound sensitivity; not probabilistic propagation"
                ),
            }
        )
    return output
