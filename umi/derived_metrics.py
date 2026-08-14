from __future__ import annotations

from statistics import median

from umi.provenance import select_best_tier
from umi.schemas import AggregationStatistic, EfficiencyMeasurement

EFFICIENCY_ATTRIBUTES = {
    "effective_tokens": "mean_total_tokens",
    "effective_turns": "mean_turns",
    "effective_wall_time": "mean_wall_seconds",
    "effective_tool_calls": "mean_tool_calls",
}


def success_adjusted(value: float | None, success_rate: float) -> float | None:
    if value is None:
        return None
    return float("inf") if success_rate == 0 else float(value) / success_rate


def derive_efficiency_metric(record: EfficiencyMeasurement, metric: str) -> float | None:
    if record.aggregation_statistic != AggregationStatistic.ARITHMETIC_MEAN:
        return None
    attribute = EFFICIENCY_ATTRIBUTES[metric]
    return success_adjusted(getattr(record, attribute), record.success_rate)


def consolidate_derived(
    records: list[EfficiencyMeasurement], metric: str
) -> tuple[float | None, list[EfficiencyMeasurement], bool]:
    candidates = [
        record for record in records if derive_efficiency_metric(record, metric) is not None
    ]
    if not candidates:
        return None, [], len(records) > 1
    selected = list(select_best_tier(candidates))
    values = [derive_efficiency_metric(record, metric) for record in selected]
    present = [float(value) for value in values if value is not None]
    return (median(present) if present else None, selected, len(candidates) > 1)


def consolidate_cost_per_success(
    records: list[EfficiencyMeasurement],
) -> tuple[float | None, list[EfficiencyMeasurement], bool]:
    candidates = [
        record
        for record in records
        if record.mean_cost_per_attempt is not None
        and record.aggregation_statistic == AggregationStatistic.ARITHMETIC_MEAN
    ]
    if not candidates:
        return None, [], len(records) > 1
    selected = list(select_best_tier(candidates))
    values = [
        success_adjusted(record.mean_cost_per_attempt, record.success_rate) for record in selected
    ]
    present = [float(value) for value in values if value is not None]
    return (median(present) if present else None, selected, len(candidates) > 1)
