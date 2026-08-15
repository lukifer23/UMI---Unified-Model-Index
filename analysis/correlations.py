from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from statistics import median

import numpy as np
from scipy.stats import pearsonr, spearmanr

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.provenance import select_best_tier
from umi.readiness import scoring_dataset
from umi.schemas import BenchmarkMeasurement, Direction


@dataclass(frozen=True)
class CorrelationResult:
    benchmark_a: str
    benchmark_b: str
    cohort_a: str
    cohort_b: str
    pearson: float | None
    spearman: float | None
    overlap: int
    interpretable: bool
    family_a: str | None = None
    family_b: str | None = None
    known_overlap: bool = False
    direction_a: str | None = None
    direction_b: str | None = None
    interpretability_reason: str | None = None


def benchmark_correlations(
    dataset: Dataset, minimum_overlap: int = 5, config: ProjectConfig | None = None
) -> list[CorrelationResult]:
    if config is not None:
        dataset, _ = scoring_dataset(dataset)
    definitions = {item.id: item for item in config.benchmarks} if config else {}
    grouped: dict[tuple[str, str, str], list[BenchmarkMeasurement]] = {}
    for item in dataset.benchmarks:
        grouped.setdefault((item.benchmark_id, item.cohort_key, item.model_id), []).append(item)
    matrix: dict[tuple[str, str], dict[str, float]] = {}
    for (benchmark_id, cohort_key, model_id), records in grouped.items():
        selected = select_best_tier(records)
        value = median(
            float(item.value) for item in selected
        )
        definition = definitions.get(benchmark_id)
        matrix.setdefault((benchmark_id, cohort_key), {})[model_id] = (
            -value if definition and definition.direction == Direction.LOWER else value
        )
    output: list[CorrelationResult] = []
    for key_a, key_b in combinations(sorted(matrix), 2):
        benchmark_a, cohort_a = key_a
        benchmark_b, cohort_b = key_b
        models = sorted(set(matrix[key_a]) & set(matrix[key_b]))
        overlap = len(models)
        pearson = spearman = None
        constant_series = False
        if overlap >= minimum_overlap:
            values_a = np.asarray([matrix[key_a][model] for model in models])
            values_b = np.asarray([matrix[key_b][model] for model in models])
            constant_series = np.ptp(values_a) == 0 or np.ptp(values_b) == 0
            if not constant_series:
                pearson = float(pearsonr(values_a, values_b).statistic)
                spearman = float(spearmanr(values_a, values_b).statistic)
        definition_a = definitions.get(benchmark_a)
        definition_b = definitions.get(benchmark_b)
        known_overlap = bool(
            definition_a
            and definition_b
            and (
                definition_a.family == definition_b.family
                or benchmark_b in definition_a.constituents
                or benchmark_a in definition_b.constituents
            )
        )
        incompatible_cohort = benchmark_a == benchmark_b and cohort_a != cohort_b
        reason = (
            "insufficient_overlap"
            if overlap < minimum_overlap
            else "constant_series"
            if constant_series
            else "incompatible_cohort"
            if incompatible_cohort
            else "known_overlap"
            if known_overlap
            else None
        )
        interpretable = reason is None and pearson is not None and spearman is not None
        if not interpretable:
            pearson = spearman = None
        output.append(
            CorrelationResult(
                benchmark_a,
                benchmark_b,
                cohort_a,
                cohort_b,
                pearson,
                spearman,
                overlap,
                interpretable,
                definition_a.family if definition_a else None,
                definition_b.family if definition_b else None,
                known_overlap,
                definition_a.direction.value if definition_a else None,
                definition_b.direction.value if definition_b else None,
                reason,
            )
        )
    return output
