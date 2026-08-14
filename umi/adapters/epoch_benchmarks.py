from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, datetime
from pathlib import Path

from umi.adapters.common import exact_entry, identifier
from umi.adapters.models import AdaptationResult, AdapterRejection
from umi.schemas import (
    ArtifactCaptureType,
    BenchmarkMeasurement,
    ConfigurationVerification,
    MeasurementUncertainty,
    ModelCrosswalk,
    ResultType,
    ScoringDisposition,
    SignalRole,
    Source,
    UncertaintyKind,
)

PILOT_SOURCE_MODELS = {
    "claude-opus-5_max",
    "claude-fable-5_max",
    "gpt-5.6-sol_max",
    "kimi-k3_max",
    "glm-5.2_max",
}


def adapt_epoch_gpqa_zip(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
) -> AdaptationResult:
    """Adapt the exact pilot rows from Epoch's frozen GPQA Diamond export."""
    source = Source.model_validate(
        {
            "organization": "Epoch AI",
            "url": "https://epoch.ai/data/benchmark_data.zip",
            "accessed": date(2026, 8, 14),
        }
    )
    with zipfile.ZipFile(path) as archive:
        payload = archive.read("gpqa_diamond.csv").decode("utf-8")

    records: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []
    for row in csv.DictReader(io.StringIO(payload)):
        source_model_id = row["Model version"]
        if source_model_id not in PILOT_SOURCE_MODELS:
            continue
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        evaluated = datetime.fromisoformat(row["Started at"].replace("Z", "+00:00")).date()
        records.append(
            BenchmarkMeasurement(
                record_id=identifier(f"epoch-gpqa-{match.canonical_model_id}-{row['id']}"),
                benchmark_id="gpqa-diamond",
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=float(row["mean_score"]) * 100.0,
                cohort_key="epoch-gpqa-diamond-1.0.6-simple-evals",
                evaluation_date=evaluated,
                model_release_date=date.fromisoformat(row["Release date"]),
                measurement_as_of_date=date(2026, 8, 14),
                evaluation_settings={
                    "prompt_family": "simple-evals-zero-shot-chain-of-thought",
                    "answer_format": "ANSWER: LETTER",
                    "temperature": "provider_api_default",
                    "question_count": 198,
                    "source_run_id": row["id"],
                    "logs_url": row["Logs"] or None,
                },
                number_of_tasks=198,
                uncertainty=MeasurementUncertainty(
                    kind=UncertaintyKind.STANDARD_ERROR,
                    standard_error=float(row["stderr"]) * 100.0,
                    source_fields=("stderr",),
                    notes="Standard error published by Epoch; trial count is not inferred.",
                ),
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version="gpqa-diamond-1.0.6",
                harness_version="epoch-inspect-simple-evals-gpqa-1.0.6",
                metric_definition="Mean GPQA Diamond accuracy in percent across the published run",
                evaluator="Epoch AI",
                harness_owner="Epoch AI",
                run_executor="Epoch AI",
                raw_artifact_available=True,
                capture_type=ArtifactCaptureType.RAW_UPSTREAM_PAYLOAD,
                reproducible=False,
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="gpqa-diamond",
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                notes=(
                    "Raw Epoch export retained. Exact provider endpoint and trial count are not "
                    "claimed; those omissions do not block provisional Capability use."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="epoch-gpqa-zip-v1",
        benchmarks=tuple(records),
        rejections=tuple(rejected),
    )
