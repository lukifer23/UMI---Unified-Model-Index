from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm, rankdata

from umi.schemas import (
    Direction,
    NormalizationStrategy,
    NormalizationTrace,
    ScaleKind,
    ScoreScale,
)
from umi.version import FORMULA_VERSION, NORMALIZATION_VERSION


@dataclass(frozen=True)
class NormalizedCohort:
    scores: dict[str, float | None]
    provisional: bool
    method: str
    trace: NormalizationTrace


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def normalized_series_panel_id(
    series_identity: dict[str, str],
    values: dict[str, float],
    trace: NormalizationTrace,
    config_fingerprint: str,
) -> str:
    return _digest(
        {
            "series": series_identity,
            "values": {key: values[key] for key in sorted(values)},
            "trace": trace.model_dump(mode="json"),
            "config_fingerprint": config_fingerprint,
        }
    )


def build_score_scale(
    evidence_profile_id: str,
    normalization_panel_ids: tuple[str, ...],
    config_fingerprint: str,
) -> ScoreScale:
    scale_kind = (
        ScaleKind.STABLE_PANEL_PERCENTILE
        if len(normalization_panel_ids) == 1
        else ScaleKind.WEIGHTED_STABLE_PANEL_COMPOSITE
    )
    payload = {
        "scale_kind": scale_kind,
        "evidence_profile_id": evidence_profile_id,
        "normalization_panel_ids": normalization_panel_ids,
        "formula_version": FORMULA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "config_fingerprint": config_fingerprint,
    }
    return ScoreScale(
        id=_digest(payload),
        scale_kind=scale_kind,
        evidence_profile_id=evidence_profile_id,
        normalization_panel_ids=normalization_panel_ids,
        formula_version=FORMULA_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        config_fingerprint=config_fingerprint,
    )


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
    minimum_robust_cohort: int = 8,
    minimum_rank_cohort: int = 2,
) -> NormalizedCohort:
    def result(
        scores: dict[str, float | None],
        provisional: bool,
        method: str,
        fallback_reason: str | None,
    ) -> NormalizedCohort:
        return NormalizedCohort(
            scores,
            provisional,
            method,
            NormalizationTrace(
                requested_strategy=strategy,
                applied_strategy=method,
                cohort_size=len(values),
                minimum_robust_cohort=minimum_robust_cohort,
                minimum_rank_cohort=minimum_rank_cohort,
                fallback_reason=fallback_reason,
                log_transform=log_transform,
                direction_inverted=direction == Direction.LOWER,
                provisional=provisional,
            ),
        )

    if not values:
        return result({}, True, "unscored", "empty_panel")
    if len(values) < minimum_rank_cohort:
        return result(
            {key: None for key in values}, True, "singleton", "below_minimum_rank_cohort"
        )
    finite = {key: value for key, value in values.items() if np.isfinite(value)}
    exceptional = set(values) - set(finite)

    transformed = dict(finite)
    if log_transform:
        if any(value < 0 for value in transformed.values()):
            raise ValueError("log normalization requires nonnegative values")
        transformed = {key: float(np.log1p(value)) for key, value in transformed.items()}

    provisional = len(values) < minimum_robust_cohort
    use_percentile = (
        strategy == NormalizationStrategy.PERCENTILE
        or provisional
        or len(finite) < 2
    )
    method = "percentile"
    fallback_reason = (
        "configured_percentile"
        if strategy == NormalizationStrategy.PERCENTILE
        else "below_minimum_robust_cohort"
        if provisional
        else "fewer_than_two_finite_values"
        if len(finite) < 2
        else None
    )
    scores: dict[str, float | None]
    if not use_percentile:
        array = np.asarray(list(transformed.values()), dtype=float)
        median = float(np.median(array))
        mad = float(np.median(np.abs(array - median)))
        if mad == 0:
            use_percentile = True
            method = "percentile_zero_mad"
            fallback_reason = "zero_mad"
        else:
            scale = 1.4826 * mad
            scores = {}
            for key, value in transformed.items():
                z = (value - median) / scale
                score = 100.0 * float(norm.cdf(z))
                scores[key] = score if direction == Direction.HIGHER else 100.0 - score
            method = "robust_z"
    if use_percentile:
        percentile_values = {
            key: (float(np.log1p(value)) if log_transform and np.isfinite(value) else value)
            for key, value in values.items()
        }
        scores = _percentiles(percentile_values, direction)

    for key in (exceptional if not use_percentile else ()):
        # Positive infinity is the explicit worst outcome for lower-is-better metrics.
        scores[key] = 0.0 if direction == Direction.LOWER and values[key] > 0 else 100.0
    return result(scores, provisional, method, fallback_reason)
