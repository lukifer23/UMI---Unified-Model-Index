from __future__ import annotations

from dataclasses import dataclass

from umi.loading import Dataset


@dataclass(frozen=True)
class ReferenceObservation:
    record_id: str
    model_id: str
    measurement_type: str
    metric_id: str
    value: float
    unit_or_basis: str
    cohort_key: str
    scoring_role: str


def reference_observations(dataset: Dataset) -> list[ReferenceObservation]:
    rows = [
        ReferenceObservation(
            item.record_id,
            item.model_id,
            "external_index",
            item.index_id,
            item.value,
            item.unit.value,
            item.cohort_key,
            "reference_only",
        )
        for item in dataset.external_indexes
    ]
    rows.extend(
        ReferenceObservation(
            item.record_id,
            item.model_id,
            "task_economics",
            item.workload,
            item.mean_cost_usd,
            item.cost_basis.value,
            item.cohort_key,
            (
                "headline_economics_candidate"
                if item.cost_basis.value == "successful_task"
                else "reference_only"
            ),
        )
        for item in dataset.task_economics
    )
    return sorted(rows, key=lambda item: (item.measurement_type, item.metric_id, item.model_id))
