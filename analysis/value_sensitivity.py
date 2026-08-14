from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import rankdata

from umi.config import ProjectConfig
from umi.schemas import ScoringResult, ValueFormula
from umi.value import value_score


@dataclass(frozen=True)
class ValueSensitivityResult:
    model_id: str
    baseline_rank: float | None
    rank_min: float | None
    rank_max: float | None
    score_min: float | None
    score_max: float | None


def _required_value(result: ScoringResult, formula: ValueFormula, config: ProjectConfig) -> float:
    score = value_score(
        result.capability.score,
        result.economics.score,
        formula,
        config.value.alpha,
    )
    if score is None:
        raise ValueError("Value sensitivity candidate is missing a required component")
    return score


def analyze_value_sensitivity(
    results: list[ScoringResult], config: ProjectConfig
) -> list[ValueSensitivityResult]:
    candidates = [
        item
        for item in results
        if item.capability.score is not None and item.economics.score is not None
    ]
    scores_by_formula: dict[ValueFormula, dict[str, float]] = {
        formula: {item.model_id: _required_value(item, formula, config) for item in candidates}
        for formula in config.value.sensitivity_formulas
    }
    ranks_by_formula: dict[ValueFormula, dict[str, float]] = {}
    for formula, formula_scores in scores_by_formula.items():
        ids = sorted(formula_scores)
        ranks = rankdata([-formula_scores[item] for item in ids], method="average")
        ranks_by_formula[formula] = dict(zip(ids, map(float, ranks), strict=True))
    output = []
    for item in sorted(candidates, key=lambda value: value.model_id):
        model_scores = [values[item.model_id] for values in scores_by_formula.values()]
        ranks = [values[item.model_id] for values in ranks_by_formula.values()]
        output.append(
            ValueSensitivityResult(
                item.model_id,
                ranks_by_formula[config.value.baseline][item.model_id],
                min(ranks),
                max(ranks),
                min(model_scores),
                max(model_scores),
            )
        )
    return output
