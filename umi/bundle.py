from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from umi.config import ProjectConfig, load_project_config
from umi.loading import (
    Dataset,
    SourceRegistry,
    load_dataset,
    load_model_crosswalk,
    load_source_registry,
)
from umi.schemas import (
    BenchmarkMeasurement,
    CrosswalkStatus,
    EfficiencyMeasurement,
    ModelCrosswalk,
    ScoringDisposition,
    TaskEconomicsMeasurement,
)
from umi.source_policy import validate_crosswalk, validate_overlap
from umi.validation import DataValidationError, validate_dataset, validate_source_registry


@dataclass(frozen=True)
class ScoringBundle:
    """Governed real-data inputs that passed source, identity, and policy validation."""

    dataset: Dataset
    config: ProjectConfig
    source_registry: SourceRegistry
    crosswalk: ModelCrosswalk
    registry_path: Path
    warnings: tuple[str, ...] = ()


def validate_scoring_bundle(
    dataset: Dataset,
    config: ProjectConfig,
    registry: SourceRegistry,
    registry_path: str | Path,
    crosswalk: ModelCrosswalk,
) -> tuple[str, ...]:
    errors: set[str] = set(validate_dataset(dataset, config).errors)
    registry_report = validate_source_registry(registry, registry_path, dataset)
    errors.update(registry_report.errors)
    crosswalk_report = validate_crosswalk(crosswalk, dataset, registry)
    errors.update(crosswalk_report.errors)
    errors.update(validate_overlap(config.overlap).errors)

    signals = {item.id: item for item in config.overlap.signals}
    definitions = {item.id: item for item in config.benchmarks}
    entries = {item.id: item for item in crosswalk.entries}
    snapshots = {item.id: item for item in registry.snapshots}
    records: tuple[
        BenchmarkMeasurement | EfficiencyMeasurement | TaskEconomicsMeasurement, ...
    ] = (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
    for record in records:
        if record.scoring_disposition != ScoringDisposition.SCORED:
            continue
        prefix = f"record {record.record_id}"
        if record.capture_type is None:
            errors.add(f"{prefix} lacks capture_type")
        if record.signal_id is None:
            errors.add(f"{prefix} lacks signal_id")
        else:
            signal = signals.get(record.signal_id)
            if signal is None:
                errors.add(f"{prefix} references unknown signal policy")
            else:
                if signal.disposition != ScoringDisposition.SCORED:
                    errors.add(f"{prefix} signal policy does not permit scoring")
                if signal.role != record.signal_role:
                    errors.add(f"{prefix} role differs from signal policy")
        if isinstance(record, BenchmarkMeasurement):
            definition = definitions.get(record.benchmark_id)
            if definition is None:
                errors.add(f"{prefix} references unknown benchmark definition")
            elif record.signal_id != definition.signal_id:
                errors.add(f"{prefix} signal differs from benchmark definition")

        artifact_id = record.source_registry_snapshot_id
        if artifact_id is None or artifact_id != record.source_artifact_id:
            errors.add(f"{prefix} lacks an exact source-registry snapshot binding")
        snapshot = snapshots.get(artifact_id or "")
        if snapshot is None:
            errors.add(f"{prefix} references an unknown source-registry snapshot")

        entry = entries.get(record.crosswalk_entry_id or "")
        if entry is None:
            errors.add(f"{prefix} lacks an exact crosswalk binding")
        else:
            if entry.status != CrosswalkStatus.EXACT:
                errors.add(f"{prefix} crosswalk entry is not exact")
            if entry.canonical_model_id != record.model_id:
                errors.add(f"{prefix} crosswalk model differs from record model")
            if entry.source_artifact_id != record.source_artifact_id:
                errors.add(f"{prefix} crosswalk artifact differs from record artifact")
            if snapshot is not None and entry.upstream_revision != snapshot.upstream_revision:
                errors.add(f"{prefix} crosswalk revision differs from source registry")
    return tuple(sorted(errors))


def load_scoring_bundle(
    data_dir: str | Path,
    config_dir: str | Path,
    source_registry_path: str | Path,
    crosswalk_path: str | Path,
) -> ScoringBundle:
    dataset = load_dataset(data_dir)
    if any(model.synthetic for model in dataset.models):
        raise DataValidationError(("synthetic fixtures cannot enter the real-data bundle path",))
    config = load_project_config(config_dir)
    registry_path = Path(source_registry_path)
    registry = load_source_registry(registry_path)
    crosswalk = load_model_crosswalk(crosswalk_path)
    errors = validate_scoring_bundle(dataset, config, registry, registry_path, crosswalk)
    if errors:
        raise DataValidationError(errors)
    reports = (
        validate_dataset(dataset, config),
        validate_source_registry(registry, registry_path, dataset),
        validate_crosswalk(crosswalk, dataset, registry),
    )
    warnings = tuple(sorted({warning for report in reports for warning in report.warnings}))
    return ScoringBundle(dataset, config, registry, crosswalk, registry_path, warnings)
