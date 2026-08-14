from __future__ import annotations

from collections import defaultdict
from statistics import median

from analysis.pareto import ParetoPoint, ParetoResult, pareto_frontier
from umi.loading import Dataset
from umi.provenance import select_best_tier
from umi.schemas import EfficiencyMeasurement, ScoringResult


def _median_by_model(
    records: tuple[EfficiencyMeasurement, ...], attribute: str, success_adjusted: bool = False
) -> dict[str, float]:
    grouped: dict[str, list[EfficiencyMeasurement]] = defaultdict(list)
    for record in records:
        if getattr(record, attribute) is not None:
            grouped[record.model_id].append(record)
    output = {}
    for model_id, items in grouped.items():
        selected = select_best_tier(items)
        values = []
        for item in selected:
            value = float(getattr(item, attribute))
            if success_adjusted:
                value = float("inf") if item.success_rate == 0 else value / item.success_rate
            values.append(value)
        output[model_id] = median(values)
    return output


def pareto_dimensions(
    dataset: Dataset, results: list[ScoringResult]
) -> dict[str, list[ParetoResult]]:
    capability = {item.model_id: item.capability.score for item in results}
    expenses = {
        "cost_per_success": _median_by_model(dataset.efficiency, "mean_cost_per_attempt", True),
        "effective_tokens": _median_by_model(dataset.efficiency, "mean_total_tokens", True),
        "latency": _median_by_model(dataset.efficiency, "mean_wall_seconds"),
    }
    output = {}
    for name, values in expenses.items():
        points = []
        for model_id, expense in values.items():
            capability_value = capability.get(model_id)
            if capability_value is not None:
                points.append(ParetoPoint(model_id, capability_value, expense))
        output[name] = pareto_frontier(points)
    return output
