from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import ComponentScore, Direction, EfficiencyMeasurement, Provenance


def score_economics(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    grouped: dict[tuple[str, str], list[EfficiencyMeasurement]] = defaultdict(list)
    for item in dataset.efficiency:
        grouped[(item.workload, item.model_id)].append(item)
    model_scores: dict[str, list[float]] = defaultdict(list)
    evidence: dict[str, list[Provenance]] = defaultdict(list)
    provisional: dict[str, bool] = defaultdict(bool)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    for workload in sorted({key[0] for key in grouped}):
        costs: dict[str, float] = {}
        for (candidate, model_id), records in grouped.items():
            if candidate != workload:
                continue
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
                model_scores[model_id].append(score)
                provisional[model_id] |= normalized.provisional

    output: dict[str, ComponentScore] = {}
    for model in dataset.models:
        scores = model_scores.get(model.id, [])
        records_by_id = {item.record_id: item for item in evidence[model.id]}
        output[model.id] = ComponentScore(
            score=sum(scores) / len(scores) if scores else None,
            coverage=1.0 if scores else 0.0,
            provisional=provisional[model.id],
            source_record_ids=tuple(sorted(records_by_id)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
        )
    return ComponentComputation(output, {key: tuple(value) for key, value in evidence.items()}, {})
