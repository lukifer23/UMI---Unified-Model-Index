from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, ConfigDict

from umi.config import ProjectConfig
from umi.loading import Dataset, SourceRegistry
from umi.readiness import is_scoring_ready
from umi.schemas import (
    BenchmarkMeasurement,
    CrosswalkStatus,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    ModelCrosswalk,
    ModelCrosswalkEntry,
    OverlapPolicy,
    ScoringDisposition,
    TaskEconomicsMeasurement,
)


class PolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PolicyReport(PolicyModel):
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class SourceReadinessRow(PolicyModel):
    record_id: str
    model_id: str
    source_artifact_id: str | None
    disposition: str
    scoring_ready: bool
    failures: tuple[str, ...] = ()


def validate_crosswalk(
    crosswalk: ModelCrosswalk,
    dataset: Dataset | None = None,
    registry: SourceRegistry | None = None,
) -> PolicyReport:
    errors: list[str] = []
    warnings: list[str] = []
    exact = [item for item in crosswalk.entries if item.status == CrosswalkStatus.EXACT]
    ids = [item.id for item in crosswalk.entries]
    if len(ids) != len(set(ids)):
        errors.append("crosswalk entry IDs must be unique")
    source_keys = [
        (item.source_id, item.source_artifact_id, item.source_model_id) for item in exact
    ]
    if len(source_keys) != len(set(source_keys)):
        errors.append("one source model row cannot map to multiple canonical configurations")
    canonical_by_source: dict[tuple[str, str], list[ModelCrosswalkEntry]] = defaultdict(list)
    for item in exact:
        if item.canonical_model_id is not None:
            canonical_by_source[(item.source_id, item.canonical_model_id)].append(item)
    for (source_id, model_id), entries in sorted(canonical_by_source.items()):
        if len(entries) > 1:
            errors.append(f"source {source_id} maps multiple rows to canonical model {model_id}")
    if dataset is not None:
        models = {model.id: model for model in dataset.models}
        for item in exact:
            model = models.get(item.canonical_model_id or "")
            if model is None:
                errors.append(f"crosswalk {item.id} references unknown canonical model")
            elif item.canonical_effort != model.configuration:
                errors.append(f"crosswalk {item.id} effort differs from canonical model")
    if registry is not None:
        snapshots = {item.id: item for item in registry.snapshots}
        for item in crosswalk.entries:
            snapshot = snapshots.get(item.source_artifact_id)
            if snapshot is None:
                errors.append(f"crosswalk {item.id} references unknown source artifact")
            elif snapshot.upstream_revision != item.upstream_revision:
                errors.append(f"crosswalk {item.id} upstream revision mismatch")
    if not exact:
        warnings.append("crosswalk contains no exact matches")
    return PolicyReport(
        valid=not errors,
        errors=tuple(sorted(set(errors))),
        warnings=tuple(warnings),
    )


def validate_overlap(policy: OverlapPolicy) -> PolicyReport:
    # ProjectConfig performs the authoritative graph and budget validation.
    signals = {item.id for item in policy.signals}
    errors = [
        f"overlap edge references unknown signal: {edge.source}->{edge.target}"
        for edge in policy.edges
        if edge.source not in signals or edge.target not in signals
    ]
    return PolicyReport(valid=not errors, errors=tuple(sorted(set(errors))))


def source_readiness_matrix(dataset: Dataset) -> tuple[SourceReadinessRow, ...]:
    models = {item.id: item for item in dataset.models}
    records: tuple[
        BenchmarkMeasurement
        | EfficiencyMeasurement
        | TaskEconomicsMeasurement
        | ExternalIndexMeasurement,
        ...,
    ] = (
        *dataset.benchmarks,
        *dataset.efficiency,
        *dataset.task_economics,
        *dataset.external_indexes,
    )
    rows: list[SourceReadinessRow] = []
    for record in sorted(records, key=lambda item: item.record_id):
        model_id = record.model_id
        model = models.get(model_id)
        failures: tuple[str, ...]
        if record.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY:
            failures = ("signal policy is diagnostic-only",)
        elif model is None:
            failures = ("unknown canonical model",)
        else:
            from umi.readiness import readiness_failures

            failures = readiness_failures(record, model)
        rows.append(
            SourceReadinessRow(
                record_id=record.record_id,
                model_id=model_id,
                source_artifact_id=record.source_artifact_id,
                disposition=record.scoring_disposition.value,
                scoring_ready=(
                    model is not None
                    and record.scoring_disposition == ScoringDisposition.SCORED
                    and is_scoring_ready(record, model)
                ),
                failures=failures,
            )
        )
    return tuple(rows)


def overlap_report(config: ProjectConfig) -> dict[str, object]:
    return {
        "config_fingerprint": config.fingerprint,
        "signals": [item.model_dump(mode="json") for item in config.overlap.signals],
        "edges": [item.model_dump(mode="json") for item in config.overlap.edges],
    }
