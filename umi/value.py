from __future__ import annotations

from math import sqrt


def value_score(capability: float | None, cost_efficiency: float | None) -> float | None:
    if capability is None or cost_efficiency is None:
        return None
    return sqrt(max(capability, 0.0) * max(cost_efficiency, 0.0))
