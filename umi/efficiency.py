from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric, weighted_available
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import ComponentScore, Direction, EfficiencyMeasurement, Provenance

METRICS = {
    "effective_tokens": "mean_total_tokens",
    "turns": "mean_turns",
    "wall_seconds": "mean_wall_seconds",
    "tool_calls": "mean_tool_calls",
}


def _selected_records(dataset: Dataset) -> dict[tuple[str, str, str], list[EfficiencyMeasurement]]:
    grouped: dict[tuple[str, str, str], list[EfficiencyMeasurement]] = defaultdict(list)
    for item in dataset.efficiency:
        grouped[(item.workload, item.cohort_key, item.model_id)].append(item)
    return grouped


def score_efficiency(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    grouped = _selected_records(dataset)
    metric_category_scores: dict[str, dict[str, dict[str, list[float]]]] = {
        metric: defaultdict(lambda: defaultdict(list)) for metric in METRICS
    }
    selected_by_model: dict[str, list[Provenance]] = defaultdict(list)
    provisional_by_model: dict[str, bool] = defaultdict(bool)
    diagnostics: dict[str, list[str]] = defaultdict(list)

    for workload, cohort_key in sorted({(key[0], key[1]) for key in grouped}):
        consolidated: dict[str, dict[str, float]] = {metric: {} for metric in METRICS}
        categories: dict[str, str] = {}
        for (candidate_workload, candidate_cohort, model_id), records in grouped.items():
            if candidate_workload != workload or candidate_cohort != cohort_key:
                continue
            categories[model_id] = records[0].workload_category.value
            best = []
            for metric, attribute in METRICS.items():
                value, selected, conflict = consolidate_numeric(records, attribute)
                best.extend(selected)
                if value is None:
                    continue
                if metric == "effective_tokens":
                    success, _, _ = consolidate_numeric(records, "success_rate")
                    if success is None:
                        continue
                    value = float("inf") if success == 0 else value / success
                consolidated[metric][model_id] = value
                if conflict:
                    diagnostics[model_id].append(f"conflict consolidated for efficiency/{workload}")
            selected_by_model[model_id].extend(best)
        for metric, raw_values in consolidated.items():
            normalized = normalize_cohort(
                raw_values,
                direction=Direction.LOWER,
                log_transform=metric in config.normalization.log_metrics,
                minimum_robust_cohort=config.normalization.minimum_robust_cohort,
                minimum_rank_cohort=config.normalization.minimum_rank_cohort,
            )
            for model_id, score in normalized.scores.items():
                if score is not None:
                    metric_category_scores[metric][categories[model_id]][model_id].append(score)
                    provisional_by_model[model_id] |= normalized.provisional

    output: dict[str, ComponentScore] = {}
    for model in dataset.models:
        category_values: dict[str, float | None] = {}
        for category in config.weights.workload_weights:
            metric_values = {}
            for metric in METRICS:
                scores = metric_category_scores[metric].get(category.value, {}).get(model.id, [])
                metric_values[metric] = sum(scores) / len(scores) if scores else None
            category_values[category.value], _ = weighted_available(
                metric_values, config.weights.efficiency
            )
        score, coverage = weighted_available(
            category_values,
            {key.value: value for key, value in config.weights.workload_weights.items()},
        )
        represented = sum(value is not None for value in category_values.values())
        records_by_id = {item.record_id: item for item in selected_by_model[model.id]}
        output[model.id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=provisional_by_model[model.id],
            source_record_ids=tuple(sorted(records_by_id)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
            coverage_details={
                "efficiency_workloads_represented": represented,
                "efficiency_workloads_total": len(config.weights.workload_weights),
                "efficiency_workload_weighted": coverage,
            },
        )
    return ComponentComputation(
        output, {key: tuple(value) for key, value in selected_by_model.items()}, {}
    )
