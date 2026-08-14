from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import rankdata

from umi.schemas import ScoringResult


@dataclass(frozen=True)
class RankedResult:
    rank: float | None
    result: ScoringResult


def rank_results(
    results: list[ScoringResult], *, metric: str = "overall", eligible_only: bool = True
) -> list[RankedResult]:
    candidates = [item for item in results if not eligible_only or item.eligible]
    values: list[tuple[ScoringResult, float]] = []
    unscored: list[ScoringResult] = []
    for item in candidates:
        value = getattr(item, metric)
        if value is None:
            unscored.append(item)
        else:
            values.append((item, float(value)))
    ranks = rankdata([-value for _, value in values], method="average") if values else []
    ranked = [
        RankedResult(float(rank), item) for (item, _), rank in zip(values, ranks, strict=True)
    ]
    ranked.sort(
        key=lambda item: (
            item.rank if item.rank is not None else float("inf"),
            item.result.model_id,
        )
    )
    ranked.extend(
        RankedResult(None, item) for item in sorted(unscored, key=lambda item: item.model_id)
    )
    return ranked
