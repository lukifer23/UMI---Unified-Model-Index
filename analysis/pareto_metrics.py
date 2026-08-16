from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass

from analysis.pareto import ParetoPoint, pareto_frontier
from umi._component import consolidate_numeric
from umi.derived_metrics import (
    EFFICIENCY_ATTRIBUTES,
    consolidate_cost_per_success,
    consolidate_derived,
)
from umi.loading import Dataset
from umi.readiness import scoring_dataset
from umi.schemas import CostBasis, EfficiencyMeasurement, ScoringResult, TaskEconomicsMeasurement


@dataclass(frozen=True)
class ScopedParetoResult:
    metric: str
    workload_category: str
    interaction_profile: str
    operational_profile_id: str
    success_definition_id: str
    workload: str
    cohort_key: str
    model_id: str
    dominated: bool
    dominator_ids: tuple[str, ...]


def pareto_dimensions(
    dataset: Dataset, results: list[ScoringResult]
) -> dict[str, object]:
    dataset, _ = scoring_dataset(dataset)
    supported = [item for item in results if item.capability.score is not None]
    profile_ids = {item.capability.evidence_profile_id for item in supported}
    scale_ids = {item.capability.score_scale_id for item in supported}
    if (
        not supported
        or len(profile_ids) != 1
        or len(scale_ids) != 1
        or None in profile_ids
        or None in scale_ids
    ):
        return {
            "status": "insufficient_common_support",
            "reason": "participating models do not share one Capability evidence profile and scale",
            "evidence_profile_id": None,
            "score_scale_id": None,
            "results": [],
        }
    evidence_profile_id = next(iter(profile_ids))
    score_scale_id = next(iter(scale_ids))
    capability = {item.model_id: item.capability.score for item in results}
    efficiency: dict[
        tuple[str, str, str, str, str, str], list[EfficiencyMeasurement]
    ] = defaultdict(list)
    for record in dataset.efficiency:
        interaction = (
            record.interaction_profile.value if record.interaction_profile else "unspecified"
        )
        operational_profile = record.operational_profile_id or "unspecified"
        success_definition = record.success_definition_id or "unspecified"
        efficiency[
            (
                record.workload,
                operational_profile,
                interaction,
                success_definition,
                record.cohort_key,
                record.model_id,
            )
        ].append(record)
    direct: dict[
        tuple[str, str, str, str, str, str], list[TaskEconomicsMeasurement]
    ] = defaultdict(list)
    for economics_record in dataset.task_economics:
        if economics_record.cost_basis == CostBasis.SUCCESSFUL_TASK:
            interaction = (
                economics_record.interaction_profile.value
                if economics_record.interaction_profile
                else "unspecified"
            )
            operational_profile = economics_record.operational_profile_id or "unspecified"
            success_definition = economics_record.success_definition_id or "unspecified"
            direct[
                (
                    economics_record.workload,
                    operational_profile,
                    interaction,
                    success_definition,
                    economics_record.cohort_key,
                    economics_record.model_id,
                )
            ].append(economics_record)

    series_values: dict[tuple[str, str, str, str, str, str, str], dict[str, float]] = defaultdict(
        dict
    )
    for (
        workload,
        operational_profile,
        interaction,
        success_definition,
        cohort,
        model_id,
    ), records in efficiency.items():
        category = records[0].workload_category.value
        for metric in EFFICIENCY_ATTRIBUTES:
            value, _, _ = consolidate_derived(records, metric)
            if value is not None:
                series_values[
                    (
                        metric,
                        category,
                        operational_profile,
                        interaction,
                        success_definition,
                        workload,
                        cohort,
                    )
                ][model_id] = value
        if (
            workload,
            operational_profile,
            interaction,
            success_definition,
            cohort,
            model_id,
        ) not in direct:
            value, _, _ = consolidate_cost_per_success(records)
            if value is not None:
                series_values[
                    (
                        "cost_per_success",
                        category,
                        operational_profile,
                        interaction,
                        success_definition,
                        workload,
                        cohort,
                    )
                ][model_id] = value
    for (
        workload,
        operational_profile,
        interaction,
        success_definition,
        cohort,
        model_id,
    ), direct_records in direct.items():
        category = direct_records[0].workload_category.value
        value, _, _ = consolidate_numeric(direct_records, "mean_cost_usd")
        if value is not None:
            series_values[
                (
                    "cost_per_success",
                    category,
                    operational_profile,
                    interaction,
                    success_definition,
                    workload,
                    cohort,
                )
            ][model_id] = value

    output: list[ScopedParetoResult] = []
    for (
        metric,
        category,
        operational_profile,
        interaction,
        success_definition,
        workload,
        cohort,
    ), values in sorted(series_values.items()):
        points = []
        for model_id, expense in values.items():
            capability_value = capability.get(model_id)
            if capability_value is not None:
                points.append(ParetoPoint(model_id, capability_value, expense))
        for result in pareto_frontier(points):
            output.append(
                ScopedParetoResult(
                    metric=metric,
                    workload_category=category,
                    interaction_profile=interaction,
                    operational_profile_id=operational_profile,
                    success_definition_id=success_definition,
                    workload=workload,
                    cohort_key=cohort,
                    model_id=result.model_id,
                    dominated=result.dominated,
                    dominator_ids=result.dominator_ids,
                )
            )
    return {
        "status": "ok",
        "reason": None,
        "evidence_profile_id": evidence_profile_id,
        "score_scale_id": score_scale_id,
        "results": [
            {
                **asdict(item),
                "evidence_profile_id": evidence_profile_id,
                "score_scale_id": score_scale_id,
            }
            for item in output
        ],
    }
