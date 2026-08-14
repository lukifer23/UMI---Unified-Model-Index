from __future__ import annotations

from math import sqrt

from umi.schemas import ValueFormula


def value_score(
    capability: float | None,
    cost_efficiency: float | None,
    formula: ValueFormula = ValueFormula.GEOMETRIC,
    alpha: float = 0.5,
) -> float | None:
    if capability is None or cost_efficiency is None:
        return None
    capability = max(capability, 0.0)
    cost_efficiency = max(cost_efficiency, 0.0)
    if formula == ValueFormula.GEOMETRIC:
        return sqrt(capability * cost_efficiency)
    if formula == ValueFormula.WEIGHTED_GEOMETRIC:
        return float(capability**alpha * cost_efficiency ** (1.0 - alpha))
    if capability + cost_efficiency == 0:
        return 0.0
    return 2.0 * capability * cost_efficiency / (capability + cost_efficiency)
