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
