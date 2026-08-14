from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import cast

from umi.adapters.common import exact_entry, identifier, load_yaml
from umi.adapters.models import AdaptationResult, AdapterRejection
from umi.schemas import (
    AggregationStatistic,
    BenchmarkMeasurement,
    Direction,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    ModelCrosswalk,
    RecordStatus,
    ResultType,
    ScoringDisposition,
    SignalRole,
    Source,
    Unit,
    WorkloadCategory,
)


def adapt_aa_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    as_of = date.fromisoformat(str(raw["as_of"]))
    records: list[ExternalIndexMeasurement] = []
    rejected: list[AdapterRejection] = []
    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        records.append(
            ExternalIndexMeasurement(
                record_id=identifier(f"aa-{row['index_id']}-{match.canonical_model_id}-{as_of}"),
                index_id=identifier(str(row["index_id"])),
                model_id=match.canonical_model_id,
                model_snapshot_id=match.canonical_model_id,
                value=float(cast(float, row["value"])),
                unit=Unit.SCORE,
                direction=Direction.HIGHER,
                cohort_key=identifier(f"aa-{row['index_version']}-{as_of}"),
                evaluation_date=as_of,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=str(row["index_version"]),
                harness_version="aa-public-page-snapshot",
                metric_definition=str(row["metric_definition"]),
                evaluator="Artificial Analysis",
                raw_artifact_available=True,
                source_artifact_id=artifact_id,
                configuration_verified=True,
                record_status=RecordStatus.DIAGNOSTIC_ONLY,
                signal_role=SignalRole.COMPOSITE,
                scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
                notes="Public-page fact capture; composite excluded from UMI scoring.",
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="aa-reviewed-facts-v1",
        external_indexes=tuple(records),
        rejections=tuple(rejected),
    )


def adapt_deepswe_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    as_of = date.fromisoformat(str(raw["as_of"]))
    benchmark_version = str(raw["benchmark_version"])
    benchmarks: list[BenchmarkMeasurement] = []
    efficiency: list[EfficiencyMeasurement] = []
    rejected: list[AdapterRejection] = []
    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        benchmarks.append(
            BenchmarkMeasurement(
                record_id=identifier(f"deepswe-score-{match.canonical_model_id}-{as_of}"),
                benchmark_id="deepswe-v1.1",
                model_id=match.canonical_model_id,
                model_snapshot_id=match.canonical_model_id,
                value=float(cast(float, row["pass_rate_percent"])),
                cohort_key=identifier(f"deepswe-v1.1-{as_of}"),
                evaluation_date=as_of,
                evaluation_settings={"agent": "mini-swe-agent", "task_count": raw["task_count"]},
                number_of_tasks=int(str(raw["task_count"])),
                confidence_interval=(
                    float(cast(float, row["pass_rate_percent"]))
                    - float(cast(float, row["confidence_interval_percent"])),
                    float(cast(float, row["pass_rate_percent"]))
                    + float(cast(float, row["confidence_interval_percent"])),
                ),
                metric_definition="DeepSWE v1.1 task resolution rate in percent",
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=benchmark_version,
                harness_version="pier-mini-swe-agent-deepswe-v1.1",
                evaluator="Datacurve",
                harness_owner="Datacurve",
                run_executor="Datacurve",
                raw_artifact_available=True,
                source_artifact_id=artifact_id,
                configuration_verified=True,
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
            )
        )
        efficiency.append(
            EfficiencyMeasurement(
                record_id=identifier(f"deepswe-resource-summary-{match.canonical_model_id}-{as_of}"),
                model_id=match.canonical_model_id,
                model_snapshot_id=match.canonical_model_id,
                workload="deepswe-v1.1",
                workload_category=WorkloadCategory.CODING,
                cohort_key=identifier(f"deepswe-v1.1-{as_of}"),
                evaluation_date=as_of,
                attempts=int(str(raw["task_count"])),
                success_rate=float(cast(float, row["pass_rate_percent"])) / 100.0,
                observed_output_tokens_summary=float(cast(float, row["output_tokens"])),
                observed_agent_steps_summary=float(cast(float, row["agent_steps"])),
                observed_cost_summary_usd=float(cast(float, row["cost_usd"])),
                aggregation_statistic=AggregationStatistic.UNSPECIFIED,
                metric_definition=(
                    "Published DeepSWE resource summaries; statistic semantics are not sufficient "
                    "for mean-based success adjustment"
                ),
                record_status=RecordStatus.DIAGNOSTIC_ONLY,
                signal_role=SignalRole.EFFICIENCY,
                scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=benchmark_version,
                harness_version="pier-mini-swe-agent-deepswe-v1.1",
                evaluator="Datacurve",
                harness_owner="Datacurve",
                run_executor="Datacurve",
                raw_artifact_available=True,
                source_artifact_id=artifact_id,
                configuration_verified=True,
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="deepswe-reviewed-facts-v1",
        benchmarks=tuple(benchmarks),
        efficiency=tuple(efficiency),
        rejections=tuple(rejected),
        diagnostics=(
            "DeepSWE resource summaries retained as diagnostic because mean semantics are unproven",
        ),
    )
