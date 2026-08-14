from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParetoPoint:
    model_id: str
    capability: float
    expense: float


@dataclass(frozen=True)
class ParetoResult:
    model_id: str
    dominated: bool
    dominator_ids: tuple[str, ...]


def pareto_frontier(points: list[ParetoPoint]) -> list[ParetoResult]:
    output: list[ParetoResult] = []
    for point in sorted(points, key=lambda item: item.model_id):
        dominators = []
        for candidate in points:
            if candidate.model_id == point.model_id:
                continue
            weakly_better = (
                candidate.capability >= point.capability and candidate.expense <= point.expense
            )
            strictly_better = (
                candidate.capability > point.capability or candidate.expense < point.expense
            )
            if weakly_better and strictly_better:
                dominators.append(candidate.model_id)
        output.append(ParetoResult(point.model_id, bool(dominators), tuple(sorted(dominators))))
    return output
