from __future__ import annotations

from dataclasses import dataclass

from analysis.rankings import rank_results
from umi.config import ProjectConfig
from umi.schemas import ScoringResult
from umi.scoring import eligible_for_weights, overall_for_weights


@dataclass(frozen=True)
class SensitivityResult:
    model_id: str
    baseline_eligible: bool
    eligible_scenario_count: int
    ineligible_scenario_count: int
    baseline_rank: float | None
    rank_min: float | None
    rank_max: float | None
    score_min: float | None
    score_max: float | None
    maximum_rank_movement: float | None
    stability: float | None
    eligibility_changed: bool


def analyze_sensitivity(
    results: list[ScoringResult], config: ProjectConfig
) -> list[SensitivityResult]:
    scenario_scores: dict[str, dict[str, float]] = {}
    scenario_ranks: dict[str, dict[str, float]] = {}
    scenario_eligibility: dict[str, set[str]] = {}
    for weights in config.weights.sensitivity_sets:
        eligible = [item for item in results if eligible_for_weights(item, config, weights)]
        scenario_eligibility[weights.name] = {item.model_id for item in eligible}
        scores = {
            item.model_id: score
            for item in eligible
            if (score := overall_for_weights(item, weights)) is not None
        }
        scenario_scores[weights.name] = scores
        temporary = [
            item.model_copy(
                update={
                    "headline_overall": scores[item.model_id],
                    "eligible": True,
                    "overall_coverage": (
                        weights.capability * item.capability.coverage
                        + weights.efficiency * item.efficiency.coverage
                        + weights.economics * item.economics.coverage
                    ),
                }
            )
            for item in eligible
            if item.model_id in scores
        ]
        scenario_ranks[weights.name] = {
            ranked.result.model_id: float(ranked.rank)
            for ranked in rank_results(temporary)
            if ranked.rank is not None
        }

    baseline_name = config.weights.sensitivity_sets[0].name
    output: list[SensitivityResult] = []
    for item in sorted(results, key=lambda value: value.model_id):
        eligible_names = [
            name for name, model_ids in scenario_eligibility.items() if item.model_id in model_ids
        ]
        ranks = [
            scenario_ranks[name][item.model_id]
            for name in eligible_names
            if item.model_id in scenario_ranks[name]
        ]
        model_scores = [
            scenario_scores[name][item.model_id]
            for name in eligible_names
            if item.model_id in scenario_scores[name]
        ]
        baseline_eligible = item.model_id in scenario_eligibility.get(baseline_name, set())
        baseline_rank = scenario_ranks.get(baseline_name, {}).get(item.model_id)
        rank_min = min(ranks) if ranks else None
        rank_max = max(ranks) if ranks else None
        denominator = max(len(results) - 1, 1)
        stability = (
            1.0 - (rank_max - rank_min) / denominator
            if rank_min is not None and rank_max is not None
            else None
        )
        movement = (
            max(abs(rank - baseline_rank) for rank in ranks)
            if baseline_rank is not None and ranks
            else None
        )
        output.append(
            SensitivityResult(
                model_id=item.model_id,
                baseline_eligible=baseline_eligible,
                eligible_scenario_count=len(eligible_names),
                ineligible_scenario_count=(
                    len(config.weights.sensitivity_sets) - len(eligible_names)
                ),
                baseline_rank=baseline_rank,
                rank_min=rank_min,
                rank_max=rank_max,
                score_min=min(model_scores) if model_scores else None,
                score_max=max(model_scores) if model_scores else None,
                maximum_rank_movement=movement,
                stability=stability,
                eligibility_changed=0 < len(eligible_names) < len(config.weights.sensitivity_sets),
            )
        )
    return output
