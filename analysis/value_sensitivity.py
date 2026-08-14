from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import rankdata

from umi.config import ProjectConfig, ValueScenario
from umi.schemas import ScoringResult
from umi.value import value_score


@dataclass(frozen=True)
class ValueSensitivityResult:
    model_id: str
    baseline_rank: float | None
    rank_min: float | None
    rank_max: float | None
    score_min: float | None
    score_max: float | None
    scenario_count: int
    maximum_rank_movement: float | None
    stability: float | None


def _required_value(result: ScoringResult, scenario: ValueScenario) -> float:
    score = value_score(
        result.capability.score,
        result.economics.score,
        scenario.formula,
        scenario.alpha if scenario.alpha is not None else 0.5,
    )
    if score is None:
        raise ValueError("Value sensitivity candidate is missing a required component")
    return score


def analyze_value_sensitivity(
    results: list[ScoringResult], config: ProjectConfig
) -> list[ValueSensitivityResult]:
    candidates = [item for item in results if item.eligible]
    scores_by_scenario = {
        scenario.name: {
            item.model_id: _required_value(item, scenario) for item in candidates
        }
        for scenario in config.value.scenarios
    }
    ranks_by_scenario: dict[str, dict[str, float]] = {}
    for name, scores in scores_by_scenario.items():
        ids = sorted(scores)
        ranks = rankdata([-scores[item] for item in ids], method="average")
        ranks_by_scenario[name] = dict(zip(ids, map(float, ranks), strict=True))
    output = []
    for item in sorted(candidates, key=lambda value: value.model_id):
        model_scores = [values[item.model_id] for values in scores_by_scenario.values()]
        ranks = [values[item.model_id] for values in ranks_by_scenario.values()]
        baseline_rank = ranks_by_scenario[config.value.baseline][item.model_id]
        rank_min, rank_max = min(ranks), max(ranks)
        movement = max(abs(rank - baseline_rank) for rank in ranks)
        denominator = max(len(candidates) - 1, 1)
        stability = 1.0 if len(candidates) == 1 else 1.0 - (rank_max - rank_min) / denominator
        output.append(
            ValueSensitivityResult(
                model_id=item.model_id,
                baseline_rank=baseline_rank,
                rank_min=rank_min,
                rank_max=rank_max,
                score_min=min(model_scores),
                score_max=max(model_scores),
                scenario_count=len(config.value.scenarios),
                maximum_rank_movement=movement,
                stability=stability,
            )
        )
    return output
