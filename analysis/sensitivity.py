from __future__ import annotations

from dataclasses import dataclass

from analysis.rankings import rank_results
from umi.config import ProjectConfig
from umi.schemas import ScoringResult
from umi.scoring import overall_for_weights


@dataclass(frozen=True)
class SensitivityResult:
    model_id: str
    baseline_rank: float | None
    rank_min: float | None
    rank_max: float | None
    score_min: float | None
    score_max: float | None
    maximum_rank_movement: float | None
    stability: float | None


def analyze_sensitivity(
    results: list[ScoringResult], config: ProjectConfig
) -> list[SensitivityResult]:
    eligible = [item for item in results if item.eligible]
    scenario_scores: dict[str, dict[str, float]] = {}
    scenario_ranks: dict[str, dict[str, float]] = {}
    for weights in config.weights.sensitivity_sets:
        scores = {
            item.model_id: score
            for item in eligible
            if (score := overall_for_weights(item, weights)) is not None
        }
        scenario_scores[weights.name] = scores
        ordered = sorted(scores, key=lambda key: (-scores[key], key))
        # Average tied ranks are delegated through temporary result copies.
        temporary = [
            item.model_copy(update={"overall": scores[item.model_id]})
            for item in eligible
            if item.model_id in scores
        ]
        scenario_ranks[weights.name] = {
            ranked.result.model_id: float(ranked.rank)
            for ranked in rank_results(temporary)
            if ranked.rank is not None
        }
        del ordered

    baseline_name = config.weights.sensitivity_sets[0].name
    output: list[SensitivityResult] = []
    for item in sorted(eligible, key=lambda value: value.model_id):
        ranks = [
            values[item.model_id] for values in scenario_ranks.values() if item.model_id in values
        ]
        model_scores = [
            values[item.model_id] for values in scenario_scores.values() if item.model_id in values
        ]
        baseline = scenario_ranks.get(baseline_name, {}).get(item.model_id)
        if not ranks or not model_scores:
            output.append(
                SensitivityResult(item.model_id, baseline, None, None, None, None, None, None)
            )
            continue
        rank_min, rank_max = min(ranks), max(ranks)
        denominator = max(len(eligible) - 1, 1)
        stability = 1.0 if len(eligible) == 1 else 1.0 - (rank_max - rank_min) / denominator
        movement = max(abs(rank - baseline) for rank in ranks) if baseline is not None else None
        output.append(
            SensitivityResult(
                item.model_id,
                baseline,
                rank_min,
                rank_max,
                min(model_scores),
                max(model_scores),
                movement,
                stability,
            )
        )
    return output
