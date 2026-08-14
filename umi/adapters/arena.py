from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import cast

from umi.adapters.common import exact_entry, identifier
from umi.adapters.models import AdaptationResult, AdapterRejection
from umi.schemas import (
    ArtifactCaptureType,
    BenchmarkMeasurement,
    ConfigurationVerification,
    Direction,
    ExternalIndexMeasurement,
    MeasurementUncertainty,
    ModelCrosswalk,
    RecordStatus,
    ResultType,
    ScoringDisposition,
    SignalRole,
    Source,
    UncertaintyKind,
    Unit,
)


def adapt_arena_json(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
    upstream_revision: str,
    subset: str,
) -> AdaptationResult:
    del upstream_revision  # validated by the crosswalk/registry contract
    with Path(path).open(encoding="utf-8") as handle:
        raw = json.load(handle)
    source = Source.model_validate(
        {
            "organization": "Arena",
            "url": "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset",
            "accessed": date(2026, 8, 14),
        }
    )
    benchmarks: list[BenchmarkMeasurement] = []
    references: list[ExternalIndexMeasurement] = []
    rejected: list[AdapterRejection] = []
    for wrapper in cast(list[dict[str, object]], raw["rows"]):
        row = cast(dict[str, object], wrapper["row"])
        source_model_id = str(row["model_name"])
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            if any(name in source_model_id for name in ("Claude", "GPT", "Kimi", "GLM")):
                rejected.append(
                    AdapterRejection(source_row_id=source_model_id, reason="no exact effort match")
                )
            continue
        published = date.fromisoformat(str(row["leaderboard_publish_date"])[:10])
        if subset == "agent":
            benchmarks.append(
                BenchmarkMeasurement(
                    record_id=identifier(f"arena-agent-{match.canonical_model_id}-{published}"),
                    benchmark_id="arena-agent",
                    model_id=match.canonical_model_id,
                    source_model_id=source_model_id,
                    value=float(cast(float, row["score"])),
                    cohort_key=identifier(f"arena-agent-ips-{published}"),
                    evaluation_date=None,
                    measurement_as_of_date=published,
                    leaderboard_publish_date=published,
                    sample_count=int(float(cast(float, row["observation_count"]))),
                    uncertainty=MeasurementUncertainty(
                        kind=UncertaintyKind.CONFIDENCE_INTERVAL,
                        lower=float(cast(float, row["score_ci_lower"])),
                        upper=float(cast(float, row["score_ci_upper"])),
                        source_fields=("score_ci_lower", "score_ci_upper"),
                        notes="The frozen artifact does not state a confidence level.",
                    ),
                    source=source,
                    result_type=ResultType.INDEPENDENT,
                    benchmark_version=f"arena-agent-{published}",
                    harness_version=f"arena-agent-ips-{published}",
                    metric_definition=(
                        "Arena Agent overall inverse-propensity-scored preference aggregate"
                    ),
                    evaluator="Arena",
                    raw_artifact_available=True,
                    capture_type=ArtifactCaptureType.ARCHIVED_SOURCE_SNAPSHOT,
                    source_artifact_id=artifact_id,
                    source_registry_snapshot_id=artifact_id,
                    crosswalk_entry_id=match.id,
                    signal_id="arena-agent",
                    configuration_verification=ConfigurationVerification(
                        model_label_exact=True,
                        release_label_exact=True,
                        effort_label_exact=True,
                        fallback_absent=True,
                    ),
                    record_status=RecordStatus.DIAGNOSTIC_ONLY,
                    signal_role=SignalRole.PREFERENCE,
                    scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
                    evaluation_settings={
                        "category": str(row["category"]),
                        "observation_count": int(float(cast(float, row["observation_count"]))),
                        "session_count": int(float(cast(float, row["session_count"]))),
                        "identity_limit": "source artifact lacks immutable snapshot/deployment",
                    },
                    notes=(
                        "Exact source model label and effort are crosswalked, but source snapshot "
                        "and deployment identity are absent; retained as diagnostic preference "
                        "evidence."
                    ),
                )
            )
        else:
            references.append(
                ExternalIndexMeasurement(
                    record_id=identifier(f"arena-text-{match.canonical_model_id}-{published}"),
                    index_id="arena-text-style-control",
                    model_id=match.canonical_model_id,
                    source_model_id=source_model_id,
                    value=float(cast(float, row["rating"])),
                    unit=Unit.SCORE,
                    direction=Direction.HIGHER,
                    cohort_key=identifier(f"arena-text-style-control-{published}"),
                    evaluation_date=None,
                    measurement_as_of_date=published,
                    leaderboard_publish_date=published,
                    source=source,
                    result_type=ResultType.INDEPENDENT,
                    benchmark_version=f"arena-text-style-control-{published}",
                    harness_version=f"arena-bradley-terry-{published}",
                    metric_definition="Arena text style-controlled Bradley-Terry rating",
                    evaluator="Arena",
                    raw_artifact_available=True,
                    capture_type=ArtifactCaptureType.ARCHIVED_SOURCE_SNAPSHOT,
                    source_artifact_id=artifact_id,
                    source_registry_snapshot_id=artifact_id,
                    crosswalk_entry_id=match.id,
                    signal_id="arena-text",
                    configuration_verification=ConfigurationVerification(
                        model_label_exact=True,
                        release_label_exact=True,
                        effort_label_exact=True,
                        fallback_absent=True,
                    ),
                    record_status=RecordStatus.DIAGNOSTIC_ONLY,
                    signal_role=SignalRole.PREFERENCE,
                    scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
                )
            )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="arena-dataset-viewer-v1",
        benchmarks=tuple(benchmarks),
        external_indexes=tuple(references),
        rejections=tuple(rejected),
    )
