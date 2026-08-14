from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, weighted_available
from umi.config import ProjectConfig
from umi.derived_metrics import EFFICIENCY_ATTRIBUTES, consolidate_derived
from umi.evidence_profiles import workload_profile
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import ComponentScore, Direction, EfficiencyMeasurement, Provenance
from umi.workloads import aggregate_workloads


def score_efficiency(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    grouped: dict[tuple[str, str, str], list[EfficiencyMeasurement]] = defaultdict(list)
    for item in dataset.efficiency:
        grouped[(item.workload, item.cohort_key, item.model_id)].append(item)

    normalized_scores: dict[str, dict[str, dict[str, list[float]]]] = {
        metric: defaultdict(lambda: defaultdict(list)) for metric in EFFICIENCY_ATTRIBUTES
    }
    selected_by_model: dict[str, list[Provenance]] = defaultdict(list)
    provisional_by_model: dict[str, set[str]] = defaultdict(set)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    profile_series: dict[str, set[str]] = defaultdict(set)
    workload_definitions = {item.id: item for item in config.workloads}
    workload_families = {item.id: item for item in config.workload_families}

    for workload, cohort_key in sorted({(workload, cohort) for workload, cohort, _ in grouped}):
        definition = workload_definitions.get(workload)
        if definition is None:
            continue
        family = workload_families[definition.family]
        raw_by_metric: dict[str, dict[str, float]] = {
            metric: {} for metric in EFFICIENCY_ATTRIBUTES
        }
        for (candidate_workload, candidate_cohort, model_id), records in grouped.items():
            if (candidate_workload, candidate_cohort) != (workload, cohort_key):
                continue
            for metric in EFFICIENCY_ATTRIBUTES:
                value, selected, conflict = consolidate_derived(records, metric)
                if value is not None:
                    raw_by_metric[metric][model_id] = value
                    selected_by_model[model_id].extend(selected)
                if conflict:
                    diagnostics[model_id].append(
                        f"conflict consolidated for efficiency/{workload}/{metric}"
                    )
        for metric, raw_values in raw_by_metric.items():
            normalized = normalize_cohort(
                raw_values,
                direction=Direction.LOWER,
                strategy=config.normalization.default_strategy,
                log_transform=metric in config.normalization.log_metrics,
                minimum_robust_cohort=config.normalization.minimum_robust_cohort,
                minimum_rank_cohort=config.normalization.minimum_rank_cohort,
            )
            for model_id, score in normalized.scores.items():
                if score is None:
                    continue
                normalized_scores[metric][workload][model_id].append(score)
                profile_series[model_id].add(
                    f"{family.category.value}/{family.id}/{workload}/{cohort_key}/{metric}"
                )
                if normalized.provisional:
                    provisional_by_model[model_id].add(f"{workload}/{cohort_key}/{metric}")

    output: dict[str, ComponentScore] = {}
    for model in dataset.models:
        category_values: dict[str, float | None] = {}
        category_coverages: dict[str, float] = {}
        family_coverages: dict[str, float] = {}
        workload_metric_cells = 0
        metric_aggregations = {
            metric: aggregate_workloads(model.id, normalized_scores[metric], config)
            for metric in config.weights.efficiency
        }
        for category in config.weights.workload_weights:
            metric_values = {
                metric: aggregation.category_scores[category.value]
                for metric, aggregation in metric_aggregations.items()
            }
            category_values[category.value], _ = weighted_available(
                metric_values, config.weights.efficiency
            )
            category_coverages[category.value] = sum(
                config.weights.efficiency[metric]
                * metric_aggregations[metric].category_coverage[category.value]
                for metric in metric_aggregations
            )
        for aggregation in metric_aggregations.values():
            workload_metric_cells += aggregation.present_cells
            for family_id, coverage_value in aggregation.family_coverage.items():
                family_coverages[family_id] = max(
                    family_coverages.get(family_id, 0.0), coverage_value
                )

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
        records_by_id = {item.record_id: item for item in selected_by_model[model.id]}
        output[model.id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=bool(provisional_ids),
            source_record_ids=tuple(sorted(records_by_id)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
            coverage_details={
                "efficiency_workloads_represented": represented,
                "efficiency_workloads_total": len(config.weights.workload_weights),
                "efficiency_workload_weighted": coverage,
                "efficiency_metric_weighted": coverage,
                "efficiency_workload_metric_cells_represented": workload_metric_cells,
                **{
                    f"efficiency_metric_coverage_{category}": value
                    for category, value in category_coverages.items()
                },
                **{
                    f"efficiency_workload_coverage_{family}": value
                    for family, value in family_coverages.items()
                },
            },
            evidence_profile=workload_profile(
                "efficiency", profile_series[model.id], records_by_id.values(), config
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
                and other_id != model_id
                and other.evidence_profile
                and other.evidence_profile.id == profile_id
            )
        )
        output[model_id] = component.model_copy(
            update={
                "directly_comparable_model_ids": peers,
                "comparability_status": (
                    "directly_comparable"
                    if peers
                    else "different_evidence_profile"
                    if has_support
                    else "insufficient_common_support"
                ),
                "comparability_reasons": (
                    ("same efficiency workload support and configuration",)
                    if peers
                    else ("no other model has the same efficiency evidence profile",)
                    if has_support
                    else ("no ready efficiency workload support",)
                ),
            }
        )
    return ComponentComputation(
        output, {key: tuple(value) for key, value in selected_by_model.items()}, {}
    )
