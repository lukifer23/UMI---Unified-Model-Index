from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from umi.adapters.common import exact_entry, identifier
from umi.adapters.models import AdaptationResult, AdapterRejection
from umi.schemas import (
    ArtifactCaptureType,
    Direction,
    ExternalIndexMeasurement,
    ModelCrosswalk,
    RecordStatus,
    ResultType,
    ScoringDisposition,
    SignalRole,
    Source,
    Unit,
)


def adapt_epoch_csv(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
) -> AdaptationResult:
    source = Source.model_validate(
        {
            "organization": "Epoch AI",
            "url": "https://epoch.ai/data/eci_benchmarks.csv",
            "accessed": date(2026, 8, 14),
        }
    )
    records: list[ExternalIndexMeasurement] = []
    rejected: list[AdapterRejection] = []
    seen_rejections: set[str] = set()
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            source_model_id = row["model_version"]
            match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
            if match is None or match.canonical_model_id is None:
                if row["Model"] in {
                    "Claude Opus 5",
                    "Claude Fable 5",
                    "GPT-5.6 Sol",
                    "Kimi K3",
                    "GLM-5.2",
                } and source_model_id not in seen_rejections:
                    rejected.append(
                        AdapterRejection(
                            source_row_id=source_model_id,
                            reason="row is not the exact reviewed effort configuration",
                        )
                    )
                    seen_rejections.add(source_model_id)
                continue
            benchmark = identifier(row["benchmark"])
            released = date.fromisoformat(row["date"])
            records.append(
                ExternalIndexMeasurement(
                    record_id=identifier(
                        f"epoch-{benchmark}-{match.canonical_model_id}-{row['model_id']}"
                    ),
                    index_id=benchmark,
                    model_id=match.canonical_model_id,
                    model_snapshot_id=match.canonical_model_id,
                    value=float(row["performance"]),
                    unit=Unit.PERCENT,
                    direction=Direction.HIGHER,
                    cohort_key=identifier(f"epoch-eci-matrix-{benchmark}-2026-08-14"),
                    evaluation_date=None,
                    model_release_date=released,
                    measurement_as_of_date=date(2026, 8, 14),
                    source=source,
                    result_type=ResultType.DERIVED,
                    benchmark_version="eci-matrix-2026-08-14",
                    harness_version="mixed-source-eci-input-matrix",
                    metric_definition=(
                        "Epoch ECI input-matrix performance; retained diagnostically because "
                        "evaluation date and harness compatibility are not established by the CSV"
                    ),
                    evaluator="Epoch AI",
                    raw_artifact_available=True,
                    capture_type=ArtifactCaptureType.RAW_UPSTREAM_PAYLOAD,
                    source_artifact_id=artifact_id,
                    source_registry_snapshot_id=artifact_id,
                    crosswalk_entry_id=match.id,
                    signal_id="epoch-eci",
                    configuration_verified=True,
                    record_status=RecordStatus.DIAGNOSTIC_ONLY,
                    signal_role=SignalRole.REFERENCE,
                    scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
                    notes=f"Original source column: {row['source'] or 'not supplied'}",
                )
            )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="epoch-eci-csv-v1",
        external_indexes=tuple(records),
        rejections=tuple(rejected),
        diagnostics=("Epoch rows are diagnostic; the ECI matrix aggregates heterogeneous sources",),
    )
