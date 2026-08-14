from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from umi.schemas import (
    BenchmarkMeasurement,
    EfficiencyMeasurement,
    ModelConfiguration,
    PricingRecord,
)


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    models: tuple[ModelConfiguration, ...]
    benchmarks: tuple[BenchmarkMeasurement, ...]
    pricing: tuple[PricingRecord, ...]
    efficiency: tuple[EfficiencyMeasurement, ...]


def _records(path: Path, key: str) -> list[object]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise ValueError(f"{path} must contain a top-level {key} list")
    return data[key]


def load_dataset(data_dir: str | Path) -> Dataset:
    root = Path(data_dir)
    return Dataset(
        models=tuple(
            ModelConfiguration.model_validate(item) for item in _records(root / "models.yaml", "models")
        ),
        benchmarks=tuple(
            BenchmarkMeasurement.model_validate(item)
            for item in _records(root / "benchmarks.yaml", "measurements")
        ),
        pricing=tuple(
            PricingRecord.model_validate(item) for item in _records(root / "pricing.yaml", "pricing")
        ),
        efficiency=tuple(
            EfficiencyMeasurement.model_validate(item)
            for item in _records(root / "task_efficiency.yaml", "measurements")
        ),
    )
