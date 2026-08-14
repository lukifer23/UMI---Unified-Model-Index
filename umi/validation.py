from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import Provenance

T = TypeVar("T")


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors

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
    model_ids = {model.id for model in dataset.models}
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
    ]
    for record_id in sorted(_duplicates([item.record_id for item in provenance])):
        errors.append(f"duplicate record id: {record_id}")

    for item in dataset.benchmarks:
        if item.model_id not in model_ids:
            errors.append(f"benchmark {item.record_id} has unknown model: {item.model_id}")
        if item.benchmark_id not in benchmark_ids:
            errors.append(f"benchmark {item.record_id} has unknown benchmark: {item.benchmark_id}")
        model = next(
            (candidate for candidate in dataset.models if candidate.id == item.model_id), None
        )
        if (
            model
            and model.snapshot_id != "unspecified"
            and item.model_snapshot_id != model.snapshot_id
        ):
            errors.append(
                f"benchmark {item.record_id} snapshot does not match model {item.model_id}"
            )
        if item.cohort_key == "unspecified":
            warnings.append(
                f"benchmark {item.record_id} is not ingestion-ready: cohort key missing"
            )
        if not item.benchmark_version or not item.harness_version:
            warnings.append(
                f"benchmark {item.record_id} is not ingestion-ready: version metadata incomplete"
            )
        if item.evaluation_date is None or item.model_snapshot_id == "unspecified":
            warnings.append(
                f"benchmark {item.record_id} is not ingestion-ready: snapshot/date missing"
            )
        if item.raw_artifact_available is not True:
            warnings.append(
                f"benchmark {item.record_id} is not ingestion-ready: raw artifact not retained"
            )
        if not item.evaluator or item.configuration_verified is not True:
            warnings.append(
                f"benchmark {item.record_id} is not ingestion-ready: "
                "evaluator/configuration unverified"
            )
    for linked_record in dataset.pricing:
        if linked_record.model_id not in model_ids:
            errors.append(
                f"record {linked_record.record_id} has unknown model: {linked_record.model_id}"
            )
    for efficiency_record in dataset.efficiency:
        if efficiency_record.model_id not in model_ids:
            errors.append(
                f"record {efficiency_record.record_id} has unknown model: "
                f"{efficiency_record.model_id}"
            )
        model = next(
            (
                candidate
                for candidate in dataset.models
                if candidate.id == efficiency_record.model_id
            ),
            None,
        )
        if (
            model
            and model.snapshot_id != "unspecified"
            and efficiency_record.model_snapshot_id != model.snapshot_id
        ):
            errors.append(
                f"record {efficiency_record.record_id} snapshot does not match model "
                f"{efficiency_record.model_id}"
            )
        if efficiency_record.cohort_key == "unspecified":
            warnings.append(
                f"record {efficiency_record.record_id} is not ingestion-ready: cohort key missing"
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

    conflicts: dict[tuple[str, str], int] = {}
    for item in dataset.benchmarks:
        key = (item.model_id, item.benchmark_id)
        conflicts[key] = conflicts.get(key, 0) + 1
    for key, count in sorted(conflicts.items()):
        if count > 1:
            warnings.append(f"conflicting benchmark measurements preserved for {key[0]}/{key[1]}")

    return ValidationReport(tuple(sorted(set(errors))), tuple(sorted(set(warnings))))
