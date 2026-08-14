from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric, weighted_available
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import ComponentScore, Direction, EfficiencyMeasurement, Provenance


def score_economics(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    grouped: dict[tuple[str, str, str], list[EfficiencyMeasurement]] = defaultdict(list)
    for item in dataset.efficiency:
        grouped[(item.workload, item.cohort_key, item.model_id)].append(item)
    category_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    evidence: dict[str, list[Provenance]] = defaultdict(list)
    provisional: dict[str, bool] = defaultdict(bool)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    for workload, cohort_key in sorted({(key[0], key[1]) for key in grouped}):
        costs: dict[str, float] = {}
        categories: dict[str, str] = {}
        for (candidate, candidate_cohort, model_id), records in grouped.items():
            if candidate != workload or candidate_cohort != cohort_key:
                continue
            categories[model_id] = records[0].workload_category.value
            cost, selected, conflict = consolidate_numeric(records, "mean_cost_per_attempt")
            success, _, _ = consolidate_numeric(records, "success_rate")
            if cost is None or success is None:
                continue
            costs[model_id] = float("inf") if success == 0 else cost / success
            evidence[model_id].extend(selected)
            if conflict:
                diagnostics[model_id].append(f"conflict consolidated for economics/{workload}")
        normalized = normalize_cohort(
            costs,
            direction=Direction.LOWER,
            log_transform=True,
            minimum_robust_cohort=config.normalization.minimum_robust_cohort,
            minimum_rank_cohort=config.normalization.minimum_rank_cohort,
        )
        for model_id, score in normalized.scores.items():
            if score is not None:
                category_scores[categories[model_id]][model_id].append(score)
                provisional[model_id] |= normalized.provisional

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
        records_by_id = {item.record_id: item for item in evidence[model.id]}
        output[model.id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=provisional[model.id],
            source_record_ids=tuple(sorted(records_by_id)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
            coverage_details={
                "economics_workloads_represented": represented,
                "economics_workloads_total": len(config.weights.workload_weights),
                "economics_workload_weighted": coverage,
            },
        )
    return ComponentComputation(output, {key: tuple(value) for key, value in evidence.items()}, {})
