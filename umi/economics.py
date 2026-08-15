from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric, weighted_available
from umi.config import ProjectConfig
from umi.derived_metrics import consolidate_cost_per_success
from umi.evidence_profiles import workload_profile
from umi.loading import Dataset
from umi.normalize import build_score_scale, normalize_cohort, normalized_series_panel_id
from umi.schemas import (
    AggregationStatistic,
    ComponentScore,
    CostBasis,
    Direction,
    EfficiencyMeasurement,
    Provenance,
    ScoreScale,
    TaskEconomicsMeasurement,
)
from umi.workloads import aggregate_workloads


def score_economics(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    efficiency: dict[tuple[str, str, str], list[EfficiencyMeasurement]] = defaultdict(list)
    for record in dataset.efficiency:
        efficiency[(record.workload, record.cohort_key, record.model_id)].append(record)
    direct: dict[tuple[str, str, str], list[TaskEconomicsMeasurement]] = defaultdict(list)
    evidence: dict[str, list[Provenance]] = defaultdict(list)
    excluded: dict[str, list[Provenance]] = defaultdict(list)
    conflicting_selected: dict[str, list[Provenance]] = defaultdict(list)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    for economics_record in dataset.task_economics:
        if (
            economics_record.cost_basis == CostBasis.SUCCESSFUL_TASK
            and economics_record.aggregation_statistic == AggregationStatistic.ARITHMETIC_MEAN
        ):
            direct[
                (
                    economics_record.workload,
                    economics_record.cohort_key,
                    economics_record.model_id,
                )
            ].append(economics_record)
        else:
            excluded[economics_record.model_id].append(economics_record)
            reason = (
                "attempted-task cost"
                if economics_record.cost_basis == CostBasis.ATTEMPTED_TASK
                else f"{economics_record.aggregation_statistic.value} cost"
            )
            diagnostics[economics_record.model_id].append(
                f"{reason} excluded from Economics/{economics_record.workload}"
            )

    normalized_scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    provisional_by_model: dict[str, set[str]] = defaultdict(set)
    profile_series: dict[str, set[str]] = defaultdict(set)
    panel_ids_by_model: dict[str, set[str]] = defaultdict(set)
    workload_definitions = {item.id: item for item in config.workloads}
    workload_families = {item.id: item for item in config.workload_families}
    series = sorted(
        {(workload, cohort) for workload, cohort, _ in efficiency}
        | {(workload, cohort) for workload, cohort, _ in direct}
    )
    for workload, cohort_key in series:
        definition = workload_definitions.get(workload)
        if definition is None:
            continue
        family = workload_families[definition.family]
        costs: dict[str, float] = {}
        for (candidate, cohort, model_id), direct_records in direct.items():
            if (candidate, cohort) != (workload, cohort_key):
                continue
            value, direct_selected, conflict = consolidate_numeric(
                direct_records, "mean_cost_usd"
            )
            if value is not None:
                costs[model_id] = value
                evidence[model_id].extend(direct_selected)
            if conflict:
                conflicting_selected[model_id].extend(direct_selected)
                diagnostics[model_id].append(f"conflict consolidated for economics/{workload}")
        for (candidate, cohort, model_id), efficiency_records in efficiency.items():
            if (candidate, cohort) != (workload, cohort_key) or (
                candidate,
                cohort,
                model_id,
            ) in direct:
                continue
            value, efficiency_selected, conflict = consolidate_cost_per_success(
                efficiency_records
            )
            if value is not None:
                costs[model_id] = value
                evidence[model_id].extend(efficiency_selected)
            if conflict:
                conflicting_selected[model_id].extend(efficiency_selected)
                diagnostics[model_id].append(f"conflict consolidated for economics/{workload}")
        normalized = normalize_cohort(
            costs,
            direction=Direction.LOWER,
            strategy=config.normalization.default_strategy,
            log_transform="cost_per_success" in config.normalization.log_metrics,
            minimum_robust_cohort=config.normalization.minimum_robust_cohort,
            minimum_rank_cohort=config.normalization.minimum_rank_cohort,
        )
        panel_id = normalized_series_panel_id(
            {
                "component": "economics",
                "workload": workload,
                "cohort_key": cohort_key,
                "metric": "cost_per_success",
            },
            costs,
            normalized.trace,
            config.fingerprint,
        )
        for model_id, score in normalized.scores.items():
            if score is None:
                continue
            normalized_scores[workload][model_id].append(score)
            panel_ids_by_model[model_id].add(panel_id)
            profile_series[model_id].add(
                f"{family.category.value}/{family.id}/{workload}/{cohort_key}/cost_per_success"
            )
            if normalized.provisional:
                provisional_by_model[model_id].add(f"{workload}/{cohort_key}/cost_per_success")

    output: dict[str, ComponentScore] = {}
    scales: dict[str, ScoreScale] = {}
    for model in dataset.models:
        aggregation = aggregate_workloads(model.id, normalized_scores, config)
        category_values = aggregation.category_scores
        category_coverages = aggregation.category_coverage
        score, _ = weighted_available(
            category_values,
            {key.value: value for key, value in config.weights.workload_weights.items()},
        )
        coverage = sum(
            weight * category_coverages[category.value]
            for category, weight in config.weights.workload_weights.items()
        )
        represented = sum(value > 0 for value in category_coverages.values())
        provisional_ids = provisional_by_model[model.id]
        if provisional_ids:
            diagnostics[model.id].append(
                "provisional normalization cohorts: " + ", ".join(sorted(provisional_ids))
            )
        records_by_id = {item.record_id: item for item in evidence[model.id]}
        profile = (
            workload_profile(
                "economics", profile_series[model.id], records_by_id.values(), config
            )
            if profile_series[model.id]
            else None
        )
        panel_ids = tuple(sorted(panel_ids_by_model[model.id]))
        scale = (
            build_score_scale(profile.id, panel_ids, config.fingerprint)
            if score is not None and profile is not None
            else None
        )
        if scale is not None:
            scales[model.id] = scale
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
                "economics_workload_cells_represented": aggregation.present_cells,
                **{
                    f"economics_category_coverage_{category}": value
                    for category, value in category_coverages.items()
                },
                **{
                    f"economics_workload_coverage_{family}": value
                    for family, value in aggregation.family_coverage.items()
                },
            },
            evidence_profile=profile,
            evidence_profile_id=profile.id if profile is not None else None,
            normalization_panel_ids=panel_ids,
            score_scale_id=scale.id if scale is not None else None,
            score_semantics=(
                "cohort-relative normalized workload composite" if score is not None else "unscored"
            ),
        )
    for model_id, component in output.items():
        profile_id = component.evidence_profile.id if component.evidence_profile else None
        has_support = bool(
            component.evidence_profile and component.evidence_profile.workload_series
        )
        peers = tuple(
            sorted(
                other_id
                for other_id, other in output.items()
                if has_support
                and component.score_scale_id is not None
                and other_id != model_id
                and other.evidence_profile_id == profile_id
                and other.score_scale_id == component.score_scale_id
            )
        )
        output[model_id] = component.model_copy(
            update={
                "directly_comparable_model_ids": peers,
                "comparability_status": (
                    "directly_comparable"
                    if peers
                    else "missing_score_scale_identity"
                    if has_support
                    else "insufficient_common_support"
                ),
                "comparability_reasons": (
                    ("same economics workload support and configuration",)
                    if peers
                    else ("economics score-scale identity is not yet emitted",)
                    if has_support
                    else ("no ready economics workload support",)
                ),
            }
        )
    return ComponentComputation(
        output,
        {key: tuple(value) for key, value in evidence.items()},
        {},
        score_scales=scales,
        excluded_candidate_evidence={
            key: tuple(value) for key, value in excluded.items()
        },
        conflicting_selected_evidence={
            key: tuple(value) for key, value in conflicting_selected.items()
        },
    )
