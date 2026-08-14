from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from umi.schemas import (
    BenchmarkMeasurement,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    ModelConfiguration,
    PricingRecord,
    SourceSnapshot,
    TaskEconomicsMeasurement,
)


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    models: tuple[ModelConfiguration, ...]
    benchmarks: tuple[BenchmarkMeasurement, ...]
    pricing: tuple[PricingRecord, ...]
    efficiency: tuple[EfficiencyMeasurement, ...]
    task_economics: tuple[TaskEconomicsMeasurement, ...]
    external_indexes: tuple[ExternalIndexMeasurement, ...]


class SourceRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    snapshots: tuple[SourceSnapshot, ...]


def _records(path: Path, key: str) -> list[object]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise ValueError(f"{path} must contain a top-level {key} list")
    return list(data[key])


def load_dataset(data_dir: str | Path) -> Dataset:
    root = Path(data_dir)
    return Dataset(
        models=tuple(
            ModelConfiguration.model_validate(item)
            for item in _records(root / "models.yaml", "models")
        ),
        benchmarks=tuple(
            BenchmarkMeasurement.model_validate(item)
            for item in _records(root / "benchmarks.yaml", "measurements")
        ),
        pricing=tuple(
            PricingRecord.model_validate(item)
            for item in _records(root / "pricing.yaml", "pricing")
        ),
        efficiency=tuple(
            EfficiencyMeasurement.model_validate(item)
            for item in _records(root / "task_efficiency.yaml", "measurements")
        ),
        task_economics=tuple(
            TaskEconomicsMeasurement.model_validate(item)
            for item in _records(root / "task_economics.yaml", "measurements")
        ),
        external_indexes=tuple(
            ExternalIndexMeasurement.model_validate(item)
            for item in _records(root / "external_indexes.yaml", "measurements")
        ),
    )


def load_source_registry(path: str | Path) -> SourceRegistry:
    return SourceRegistry(
        snapshots=tuple(
            SourceSnapshot.model_validate(item) for item in _records(Path(path), "snapshots")
        )
    )
