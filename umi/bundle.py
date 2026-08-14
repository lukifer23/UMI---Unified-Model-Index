from __future__ import annotations

import hashlib
import json
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
from umi.readiness import readiness_failures
from umi.schemas import (
    AcceptanceManifest,
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
    acceptance_manifest: AcceptanceManifest
    warnings: tuple[str, ...] = ()


def build_acceptance_manifest(
    dataset: Dataset, registry: SourceRegistry
) -> AcceptanceManifest:
    models = {item.id: item for item in dataset.models}
    records: tuple[
        BenchmarkMeasurement | EfficiencyMeasurement | TaskEconomicsMeasurement, ...
    ] = (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
    diagnostic = tuple(
        sorted(
            item.record_id
            for item in records
            if item.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY
        )
    )
    accepted_records = tuple(
        sorted(
            item.record_id
            for item in records
            if item.scoring_disposition == ScoringDisposition.SCORED
            and (model := models.get(item.model_id)) is not None
            and not readiness_failures(item, model)
        )
    )
    accepted_ids = set(accepted_records)
    accepted = tuple(item for item in records if item.record_id in accepted_ids)
    accepted_artifact_ids = tuple(
        sorted({item.source_artifact_id for item in accepted if item.source_artifact_id})
    )
    snapshots = {item.id: item for item in registry.snapshots}
    unready = tuple(
        sorted(
            item.record_id
            for item in records
            if item.scoring_disposition == ScoringDisposition.SCORED
            and item.record_id not in accepted_ids
        )
    )
    payload = {
        "accepted_record_ids": accepted_records,
        "excluded_diagnostic_record_ids": diagnostic,
        "excluded_unready_record_ids": unready,
        "accepted_artifact_ids": accepted_artifact_ids,
        "accepted_crosswalk_entry_ids": tuple(
            sorted({item.crosswalk_entry_id for item in accepted if item.crosswalk_entry_id})
        ),
        "accepted_signal_ids": tuple(
            sorted({item.signal_id for item in accepted if item.signal_id})
        ),
        "scoring_relevant_adapter_versions": tuple(
            sorted(
                {
                    snapshots[artifact_id].adapter_id
                    for artifact_id in accepted_artifact_ids
                    if artifact_id in snapshots
                }
            )
        ),
        "warnings": tuple(
            message
            for condition, message in (
                (bool(diagnostic), f"{len(diagnostic)} diagnostic records excluded"),
                (bool(unready), f"{len(unready)} unready scoring records excluded"),
            )
            if condition
        ),
    }
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return AcceptanceManifest(
        **payload,
        fingerprint=hashlib.sha256(rendered.encode()).hexdigest(),
    )


def validate_scoring_bundle(
    dataset: Dataset,
    config: ProjectConfig,
    registry: SourceRegistry,
    registry_path: str | Path,
    crosswalk: ModelCrosswalk,
) -> tuple[str, ...]:
    dataset_report = validate_dataset(dataset, config)
    errors: set[str] = set(dataset_report.errors)
    manifest = build_acceptance_manifest(dataset, registry)
    accepted_ids = set(manifest.accepted_record_ids)
    accepted_records = tuple(
        item
        for item in (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
        if item.record_id in accepted_ids
    )
    scored_artifact_ids = {
        item.source_artifact_id for item in accepted_records if item.source_artifact_id
    }
    registry_report = validate_source_registry(
        registry,
        registry_path,
        snapshot_ids=scored_artifact_ids,
    )
    errors.update(registry_report.errors)
    scored_crosswalk_ids = {
        item.crosswalk_entry_id for item in accepted_records if item.crosswalk_entry_id
    }
    scoped_crosswalk = ModelCrosswalk(
        entries=tuple(item for item in crosswalk.entries if item.id in scored_crosswalk_ids)
    )
    scored_registry = SourceRegistry(
        snapshots=tuple(item for item in registry.snapshots if item.id in scored_artifact_ids)
    )
    crosswalk_report = validate_crosswalk(scoped_crosswalk, dataset, scored_registry)
    errors.update(crosswalk_report.errors)
    errors.update(validate_overlap(config.overlap).errors)
    if set(manifest.scoring_relevant_adapter_versions) != set(dataset.adapter_versions):
        errors.add("scoring-relevant adapter versions differ from accepted source artifacts")

    signals = {item.id: item for item in config.overlap.signals}
    definitions = {item.id: item for item in config.benchmarks}
    entries = {item.id: item for item in crosswalk.entries}
    snapshots = {item.id: item for item in registry.snapshots}
    models = {item.id: item for item in dataset.models}
    records: tuple[
        BenchmarkMeasurement | EfficiencyMeasurement | TaskEconomicsMeasurement, ...
    ] = (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
    for record in records:
        if record.scoring_disposition != ScoringDisposition.SCORED:
            continue
        prefix = f"record {record.record_id}"
        model = models.get(record.model_id)
        if model is not None:
            errors.update(
                f"{prefix}: {failure}" for failure in readiness_failures(record, model)
            )
        if record.capture_type is None:
            errors.add(f"{prefix} lacks capture_type")
        verification = record.configuration_verification
        if verification is None or not all(
            (
                verification.model_label_exact,
                verification.release_label_exact,
                verification.effort_label_exact,
                verification.fallback_absent,
            )
        ):
            errors.add(f"{prefix} lacks exact structured configuration verification")
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

        if record.record_id not in accepted_ids:
            continue

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
            if entry.source_model_id != record.source_model_id:
                errors.add(f"{prefix} source model label differs from crosswalk")
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
    warnings = validate_dataset(dataset, config).warnings
    manifest = build_acceptance_manifest(dataset, registry)
    return ScoringBundle(
        dataset,
        config,
        registry,
        crosswalk,
        registry_path,
        manifest,
        tuple(sorted({*warnings, *manifest.warnings})),
    )
