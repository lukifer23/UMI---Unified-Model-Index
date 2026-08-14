from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, ConfigDict

from umi.schemas import (
    BenchmarkMeasurement,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    ModelConfiguration,
    ModelCrosswalk,
    ModelCrosswalkEntry,
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
    scored_audit_fingerprint: str | None = None
    complete_audit_fingerprint: str | None = None
    adapter_versions: tuple[str, ...] = ()


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
    audit_path = root / "audit.yaml"
    audit: dict[str, object] = {}
    if audit_path.is_file():
        with audit_path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"{audit_path} must contain a mapping")
        audit = loaded
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
        scored_audit_fingerprint=(
            str(audit["scored_audit_fingerprint"])
            if audit.get("scored_audit_fingerprint")
            else None
        ),
        complete_audit_fingerprint=(
            str(audit["complete_audit_fingerprint"])
            if audit.get("complete_audit_fingerprint")
            else None
        ),
        adapter_versions=tuple(
            str(item) for item in cast(list[object], audit.get("adapter_versions", []))
        ),
    )


def load_source_registry(path: str | Path) -> SourceRegistry:
    return SourceRegistry(
        snapshots=tuple(
            SourceSnapshot.model_validate(item) for item in _records(Path(path), "snapshots")
        )
    )


def load_model_crosswalk(path: str | Path) -> ModelCrosswalk:
    return ModelCrosswalk(
        entries=tuple(
            ModelCrosswalkEntry.model_validate(item)
            for item in _records(Path(path), "entries")
        )
    )
