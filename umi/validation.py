from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from umi.config import ProjectConfig
from umi.loading import Dataset, SourceRegistry
from umi.readiness import ScoredRecord, is_scoring_ready, readiness_failures
from umi.schemas import EfficiencyMeasurement, Provenance, RecordStatus, TaskEconomicsMeasurement

T = TypeVar("T")


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    readiness_failures: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def schema_valid(self) -> bool:
        return not self.errors

    @property
    def scoring_ready(self) -> bool:
        return self.schema_valid and not self.readiness_failures

    def raise_for_errors(self) -> None:
        if self.errors:
            raise DataValidationError(self.errors)


class DataValidationError(ValueError):
    def __init__(self, errors: tuple[str, ...] | list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def _duplicates(values: list[T]) -> set[T]:
    seen: set[T] = set()
    repeated: set[T] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return repeated


def validate_dataset(dataset: Dataset, config: ProjectConfig) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    readiness: list[str] = []
    model_ids = {model.id for model in dataset.models}
    models = {model.id: model for model in dataset.models}
    benchmark_ids = {benchmark.id for benchmark in config.benchmarks}
    family_ids = {family.id for family in config.families}

    for model_id in sorted(_duplicates([model.id for model in dataset.models])):
        errors.append(f"duplicate model id: {model_id}")
    for benchmark_id in sorted(_duplicates([item.id for item in config.benchmarks])):
        errors.append(f"duplicate benchmark id: {benchmark_id}")

    provenance: list[Provenance] = [
        *dataset.benchmarks,
        *dataset.pricing,
        *dataset.efficiency,
        *dataset.task_economics,
        *dataset.external_indexes,
    ]
    for record_id in sorted(_duplicates([item.record_id for item in provenance])):
        errors.append(f"duplicate record id: {record_id}")

    scored_inputs: tuple[ScoredRecord, ...] = (
        *dataset.benchmarks,
        *dataset.efficiency,
        *dataset.task_economics,
    )
    for item in scored_inputs:
        if item.model_id not in model_ids:
            errors.append(f"record {item.record_id} has unknown model: {item.model_id}")
            continue
        model = models[item.model_id]
        if item.record_status == RecordStatus.INVALID:
            errors.append(f"record {item.record_id} has invalid record status")
        if item.model_snapshot_id != "unspecified" and item.model_snapshot_id != model.snapshot_id:
            errors.append(f"record {item.record_id} snapshot does not match model {item.model_id}")
        for failure in readiness_failures(item, model):
            if failure != "record is diagnostic-only":
                readiness.append(f"record {item.record_id}: {failure}")
    for item in dataset.benchmarks:
        if item.benchmark_id not in benchmark_ids:
            errors.append(f"benchmark {item.record_id} has unknown benchmark: {item.benchmark_id}")
    for linked_record in dataset.pricing:
        if linked_record.model_id not in model_ids:
            errors.append(
                f"record {linked_record.record_id} has unknown model: {linked_record.model_id}"
            )
    for record in dataset.external_indexes:
        if record.model_id not in model_ids:
            errors.append(f"record {record.record_id} has unknown model: {record.model_id}")
            continue
        model = models[record.model_id]
        if record.model_snapshot_id != model.snapshot_id:
            errors.append(
                f"record {record.record_id} snapshot does not match model {record.model_id}"
            )

    if family_ids != {definition.family for definition in config.benchmarks}:
        missing = {definition.family for definition in config.benchmarks} - family_ids
        unused = family_ids - {definition.family for definition in config.benchmarks}
        errors.extend(f"benchmark references unknown family: {item}" for item in sorted(missing))
        warnings.extend(f"configured family has no benchmarks: {item}" for item in sorted(unused))
    for domain in config.weights.capability_domains:
        families = [item for item in config.families if item.domain == domain]
        if families and abs(sum(item.weight for item in families) - 1.0) > 1e-9:
            errors.append(f"family weights for {domain.value} must sum to 1")
        if any(item.weight > item.cap for item in families):
            errors.append(f"family weight exceeds cap in {domain.value}")
        if families and sum(item.cap for item in families) < 1.0 - 1e-9:
            errors.append(f"family caps for {domain.value} must sum to at least 1")
    for definition in config.benchmarks:
        family = next((item for item in config.families if item.id == definition.family), None)
        if family and family.domain != definition.domain:
            errors.append(f"benchmark {definition.id} domain does not match family {family.id}")

    for definition in config.benchmarks:
        for related in (*definition.parent_aggregates, *definition.constituents):
            if related not in benchmark_ids:
                errors.append(f"benchmark {definition.id} references unknown benchmark: {related}")
                continue
            related_definition = next(item for item in config.benchmarks if item.id == related)
            if related_definition.family != definition.family:
                errors.append(
                    f"overlapping benchmarks {definition.id} and {related} must share a family"
                )

    for model in dataset.models:
        if (
            not config.eligibility.release_start
            <= model.release_date
            <= config.eligibility.release_end
        ):
            warnings.append(f"model {model.id} is outside the configured release window")
        if model.synthetic and not (model.notes and "SYNTHETIC" in model.notes.upper()):
            warnings.append(f"synthetic model {model.id} should be conspicuously labeled in notes")

    ready_benchmark_cohorts: dict[str, set[str]] = {}
    for item in dataset.benchmarks:
        candidate_model = models.get(item.model_id)
        if candidate_model and is_scoring_ready(item, candidate_model):
            ready_benchmark_cohorts.setdefault(item.benchmark_id, set()).add(item.cohort_key)
    for benchmark_id, cohorts in sorted(ready_benchmark_cohorts.items()):
        if len(cohorts) > 1:
            errors.append(
                f"benchmark {benchmark_id} has multiple scoring cohorts without a merge policy: "
                f"{', '.join(sorted(cohorts))}"
            )
    ready_workload_cohorts: dict[tuple[str, str], set[str]] = {}
    workload_inputs: tuple[EfficiencyMeasurement | TaskEconomicsMeasurement, ...] = (
        *dataset.efficiency,
        *dataset.task_economics,
    )
    for item in workload_inputs:
        candidate_model = models.get(item.model_id)
        if candidate_model and is_scoring_ready(item, candidate_model):
            key = (item.workload_category.value, item.workload)
            ready_workload_cohorts.setdefault(key, set()).add(item.cohort_key)
    for (category, workload), cohorts in sorted(ready_workload_cohorts.items()):
        if len(cohorts) > 1:
            errors.append(
                f"workload {category}/{workload} has multiple scoring cohorts without a merge "
                f"policy: {', '.join(sorted(cohorts))}"
            )

    conflicts: dict[tuple[str, str], int] = {}
    for item in dataset.benchmarks:
        key = (item.model_id, item.benchmark_id)
        conflicts[key] = conflicts.get(key, 0) + 1
    for key, count in sorted(conflicts.items()):
        if count > 1:
            warnings.append(f"conflicting benchmark measurements preserved for {key[0]}/{key[1]}")

    return ValidationReport(
        tuple(sorted(set(errors))),
        tuple(sorted(set(warnings))),
        tuple(sorted(set(readiness))),
    )


def validate_source_registry(
    registry: SourceRegistry, registry_path: str | Path, dataset: Dataset | None = None
) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(registry_path)
    for snapshot_id in sorted(_duplicates([item.id for item in registry.snapshots])):
        errors.append(f"duplicate source snapshot id: {snapshot_id}")
    registry_urls = {str(item.source.url) for item in registry.snapshots}
    registry_ids = {item.id for item in registry.snapshots}
    registry_root = path.parent.resolve()
    for snapshot in registry.snapshots:
        if not snapshot.license_id.strip() or not snapshot.attribution.strip():
            errors.append(f"source snapshot {snapshot.id} lacks license or attribution metadata")
        if not snapshot.upstream_revision.strip() or not snapshot.adapter_id.strip():
            errors.append(f"source snapshot {snapshot.id} lacks revision or adapter metadata")
        artifact = (registry_root / snapshot.artifact_path).resolve()
        if not artifact.is_relative_to(registry_root):
            errors.append(f"source snapshot {snapshot.id} artifact escapes registry directory")
            continue
        if not artifact.is_file():
            errors.append(f"source snapshot {snapshot.id} artifact is missing: {artifact}")
            continue
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != snapshot.artifact_sha256:
            errors.append(f"source snapshot {snapshot.id} artifact checksum mismatch")
    if dataset is not None:
        for model in dataset.models:
            if not model.source_snapshot_ids:
                warnings.append(f"model {model.id} has no source snapshot references")
            for snapshot_id in model.source_snapshot_ids:
                if snapshot_id not in registry_ids:
                    errors.append(
                        f"model {model.id} references unknown source snapshot: {snapshot_id}"
                    )
        records: tuple[Provenance, ...] = (
            *dataset.benchmarks,
            *dataset.pricing,
            *dataset.efficiency,
            *dataset.task_economics,
            *dataset.external_indexes,
        )
        for record in records:
            if record.source_artifact_id and record.source_artifact_id not in registry_ids:
                errors.append(
                    f"record {record.record_id} references unknown source artifact: "
                    f"{record.source_artifact_id}"
                )
            if str(record.source.url) not in registry_urls:
                warnings.append(
                    f"record {record.record_id} source URL is absent from source registry"
                )
    return ValidationReport(tuple(sorted(set(errors))), tuple(sorted(set(warnings))))
