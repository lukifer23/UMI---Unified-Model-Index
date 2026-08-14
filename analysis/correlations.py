from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from statistics import median

import numpy as np
from scipy.stats import pearsonr, spearmanr

from umi.loading import Dataset
from umi.provenance import select_best_tier
from umi.schemas import BenchmarkMeasurement


@dataclass(frozen=True)
class CorrelationResult:
    benchmark_a: str
    benchmark_b: str
    pearson: float | None
    spearman: float | None
    overlap: int
    interpretable: bool


def benchmark_correlations(dataset: Dataset, minimum_overlap: int = 5) -> list[CorrelationResult]:
    grouped: dict[tuple[str, str], list[BenchmarkMeasurement]] = {}
    for item in dataset.benchmarks:
        grouped.setdefault((item.benchmark_id, item.model_id), []).append(item)
    matrix: dict[str, dict[str, float]] = {}
    for (benchmark_id, model_id), records in grouped.items():
        selected = select_best_tier(records)
        matrix.setdefault(benchmark_id, {})[model_id] = median(
            float(item.value) for item in selected
        )
    output: list[CorrelationResult] = []
    for benchmark_a, benchmark_b in combinations(sorted(matrix), 2):
        models = sorted(set(matrix[benchmark_a]) & set(matrix[benchmark_b]))
        overlap = len(models)
        pearson = spearman = None
        if overlap >= 2:
            values_a = np.asarray([matrix[benchmark_a][model] for model in models])
            values_b = np.asarray([matrix[benchmark_b][model] for model in models])
            if np.ptp(values_a) > 0 and np.ptp(values_b) > 0:
                pearson = float(pearsonr(values_a, values_b).statistic)
                spearman = float(spearmanr(values_a, values_b).statistic)
        output.append(
            CorrelationResult(
                benchmark_a,
                benchmark_b,
                pearson,
                spearman,
                overlap,
                overlap >= minimum_overlap and pearson is not None,
            )
        )
    return output
