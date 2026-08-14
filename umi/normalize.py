from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm, rankdata

from umi.schemas import Direction, NormalizationStrategy


@dataclass(frozen=True)
class NormalizedCohort:
    scores: dict[str, float | None]
    provisional: bool
    method: str


def _percentiles(values: dict[str, float], direction: Direction) -> dict[str, float | None]:
    keys = sorted(values)
    array = np.asarray([values[key] for key in keys], dtype=float)
    ranks = rankdata(array, method="average")
    denominator = len(keys) - 1
    scores: dict[str, float | None] = {}
    for key, rank in zip(keys, ranks, strict=True):
        score = 100.0 * (float(rank) - 1.0) / denominator
        scores[key] = score if direction == Direction.HIGHER else 100.0 - score
    return scores


def normalize_cohort(
    values: dict[str, float],
    *,
    direction: Direction,
    strategy: NormalizationStrategy = NormalizationStrategy.ROBUST_Z,
    log_transform: bool = False,
    minimum_robust_cohort: int = 5,
    minimum_rank_cohort: int = 2,
) -> NormalizedCohort:
    if not values:
        return NormalizedCohort({}, True, "unscored")
    finite = {key: value for key, value in values.items() if np.isfinite(value)}
    exceptional = set(values) - set(finite)
    if len(finite) < minimum_rank_cohort:
        return NormalizedCohort({key: None for key in values}, True, "singleton")

    transformed = dict(finite)
    if log_transform:
        if any(value < 0 for value in transformed.values()):
            raise ValueError("log normalization requires nonnegative values")
        transformed = {key: float(np.log1p(value)) for key, value in transformed.items()}

    provisional = len(finite) < minimum_robust_cohort
    use_percentile = strategy == NormalizationStrategy.PERCENTILE or provisional
    method = "percentile"
    scores: dict[str, float | None]
    if not use_percentile:
        array = np.asarray(list(transformed.values()), dtype=float)
        median = float(np.median(array))
        mad = float(np.median(np.abs(array - median)))
        if mad == 0:
            use_percentile = True
            method = "percentile_zero_mad"
        else:
            scale = 1.4826 * mad
            scores = {}
            for key, value in transformed.items():
                z = (value - median) / scale
                score = 100.0 * float(norm.cdf(z))
                scores[key] = score if direction == Direction.HIGHER else 100.0 - score
            method = "robust_z"
    if use_percentile:
        scores = _percentiles(transformed, direction)

    for key in exceptional:
        # Positive infinity is the explicit worst outcome for lower-is-better metrics.
        scores[key] = 0.0 if direction == Direction.LOWER and values[key] > 0 else 100.0
    return NormalizedCohort(scores, provisional, method)
