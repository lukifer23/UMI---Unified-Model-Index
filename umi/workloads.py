from __future__ import annotations

from dataclasses import dataclass

from umi._component import weighted_available
from umi.config import ProjectConfig


@dataclass(frozen=True)
class WorkloadAggregation:
    category_scores: dict[str, float | None]
    category_coverage: dict[str, float]
    family_coverage: dict[str, float]
    present_cells: int


def aggregate_workloads(
    model_id: str,
    scores: dict[str, dict[str, list[float]]],
    config: ProjectConfig,
) -> WorkloadAggregation:
    """Aggregate one metric through the configured workload -> family -> category hierarchy."""
    category_scores: dict[str, float | None] = {}
    category_coverage: dict[str, float] = {}
    family_coverage: dict[str, float] = {}
    present_cells = 0
    for category in config.weights.workload_weights:
        families = [item for item in config.workload_families if item.category == category]
        family_scores: dict[str, float | None] = {}
        for family in families:
            workloads = [item for item in config.workloads if item.family == family.id]
            workload_scores: dict[str, float | None] = {}
            for workload in workloads:
                values = scores.get(workload.id, {}).get(model_id, [])
                workload_scores[workload.id] = sum(values) / len(values) if values else None
                present_cells += int(bool(values))
            family_scores[family.id], family_coverage[family.id] = weighted_available(
                workload_scores, {item.id: item.weight for item in workloads}
            )
        category_scores[category.value], category_coverage[category.value] = weighted_available(
            family_scores, {item.id: item.weight for item in families}
        )
    return WorkloadAggregation(
        category_scores, category_coverage, family_coverage, present_cells
    )
