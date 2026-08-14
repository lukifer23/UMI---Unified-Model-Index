from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from umi.loading import Dataset
from umi.schemas import (
    BenchmarkMeasurement,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    ModelConfiguration,
    TaskEconomicsMeasurement,
)


class AdapterModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AdapterRejection(AdapterModel):
    source_row_id: str
    reason: str


class AdaptationResult(AdapterModel):
    source_id: str
    adapter_id: str
    benchmarks: tuple[BenchmarkMeasurement, ...] = ()
    efficiency: tuple[EfficiencyMeasurement, ...] = ()
    task_economics: tuple[TaskEconomicsMeasurement, ...] = ()
    external_indexes: tuple[ExternalIndexMeasurement, ...] = ()
    rejections: tuple[AdapterRejection, ...] = ()
    diagnostics: tuple[str, ...] = ()


def assemble_pilot_dataset(
    models: tuple[ModelConfiguration, ...], results: tuple[AdaptationResult, ...]
) -> Dataset:
    return Dataset(
        models=models,
        benchmarks=tuple(item for result in results for item in result.benchmarks),
        pricing=(),
        efficiency=tuple(item for result in results for item in result.efficiency),
        task_economics=tuple(item for result in results for item in result.task_economics),
        external_indexes=tuple(item for result in results for item in result.external_indexes),
    )
