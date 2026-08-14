from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric, weighted_available
from umi.config import ProjectConfig
from umi.derived_metrics import consolidate_cost_per_success
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import (
    ComponentScore,
    CostBasis,
    Direction,
    EfficiencyMeasurement,
    Provenance,
    TaskEconomicsMeasurement,
)


def score_economics(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    efficiency: dict[tuple[str, str, str], list[EfficiencyMeasurement]] = defaultdict(list)
    for record in dataset.efficiency:
        efficiency[(record.workload, record.cohort_key, record.model_id)].append(record)
    direct: dict[tuple[str, str, str], list[TaskEconomicsMeasurement]] = defaultdict(list)
    evidence: dict[str, list[Provenance]] = defaultdict(list)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    for economics_record in dataset.task_economics:
        if economics_record.cost_basis == CostBasis.SUCCESSFUL_TASK:
            direct[
                (
                    economics_record.workload,
                    economics_record.cohort_key,
                    economics_record.model_id,
                )
            ].append(economics_record)
        else:
            evidence[economics_record.model_id].append(economics_record)
            diagnostics[economics_record.model_id].append(
                f"attempted-task cost excluded from Economics/{economics_record.workload}"
            )

    category_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    provisional_by_model: dict[str, set[str]] = defaultdict(set)
    series = sorted(
        {(workload, cohort) for workload, cohort, _ in efficiency}
        | {(workload, cohort) for workload, cohort, _ in direct}
    )
    for workload, cohort_key in series:
        costs: dict[str, float] = {}
        categories: dict[str, str] = {}
        for (candidate, cohort, model_id), direct_records in direct.items():
            if (candidate, cohort) != (workload, cohort_key):
                continue
            categories[model_id] = direct_records[0].workload_category.value
            value, direct_selected, conflict = consolidate_numeric(
                direct_records, "mean_cost_usd"
            )
            if value is not None:
                costs[model_id] = value
                evidence[model_id].extend(direct_selected)
            if conflict:
                diagnostics[model_id].append(f"conflict consolidated for economics/{workload}")
        for (candidate, cohort, model_id), efficiency_records in efficiency.items():
            if (candidate, cohort) != (workload, cohort_key) or (
                candidate,
                cohort,
                model_id,
            ) in direct:
                continue
            categories[model_id] = efficiency_records[0].workload_category.value
            value, efficiency_selected, conflict = consolidate_cost_per_success(
                efficiency_records
            )
            if value is not None:
                costs[model_id] = value
                evidence[model_id].extend(efficiency_selected)
            if conflict:
                diagnostics[model_id].append(f"conflict consolidated for economics/{workload}")
        normalized = normalize_cohort(
            costs,
            direction=Direction.LOWER,
            strategy=config.normalization.default_strategy,
            log_transform="cost_per_success" in config.normalization.log_metrics,
            minimum_robust_cohort=config.normalization.minimum_robust_cohort,
            minimum_rank_cohort=config.normalization.minimum_rank_cohort,
        )
        for model_id, score in normalized.scores.items():
            if score is not None:
                category_scores[categories[model_id]][model_id].append(score)
                if normalized.provisional:
                    provisional_by_model[model_id].add(f"{workload}/{cohort_key}/cost_per_success")

    output: dict[str, ComponentScore] = {}
    for model in dataset.models:
        category_values = {
            category.value: (
                sum(category_scores.get(category.value, {}).get(model.id, []))
                / len(category_scores[category.value][model.id])
                if category_scores.get(category.value, {}).get(model.id)
                else None
            )
            for category in config.weights.workload_weights
        }
        score, coverage = weighted_available(
            category_values,
            {key.value: value for key, value in config.weights.workload_weights.items()},
        )
        represented = sum(value is not None for value in category_values.values())
        provisional_ids = provisional_by_model[model.id]
        if provisional_ids:
            diagnostics[model.id].append(
                "provisional normalization cohorts: " + ", ".join(sorted(provisional_ids))
            )
        records_by_id = {item.record_id: item for item in evidence[model.id]}
        output[model.id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=bool(provisional_ids),
            source_record_ids=tuple(sorted(records_by_id)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
            coverage_details={
                "economics_workloads_represented": represented,
                "economics_workloads_total": len(config.weights.workload_weights),
                "economics_workload_weighted": coverage,
            },
        )
    return ComponentComputation(output, {key: tuple(value) for key, value in evidence.items()}, {})
