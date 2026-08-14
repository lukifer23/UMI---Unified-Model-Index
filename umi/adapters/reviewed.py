from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import cast

from umi.adapters.common import exact_entry, identifier, load_yaml
from umi.adapters.models import AdaptationResult, AdapterRejection
from umi.schemas import (
    AggregationStatistic,
    ArtifactCaptureType,
    BenchmarkMeasurement,
    ConfigurationVerification,
    Direction,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    MeasurementUncertainty,
    ModelCrosswalk,
    ModelCrosswalkEntry,
    PricingRecord,
    RecordStatus,
    ReleaseClaim,
    ResultType,
    ScoringDisposition,
    SignalRole,
    Source,
    UncertaintyKind,
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
                source_model_id=source_model_id,
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
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="aa-intelligence-v4.1",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
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
                source_model_id=source_model_id,
                value=float(cast(float, row["pass_rate"])) * 100.0,
                cohort_key=identifier(f"deepswe-v1.1-{as_of}"),
                evaluation_date=as_of,
                evaluation_settings={
                    "agent": "mini-swe-agent",
                    "source_config_id": row["source_config_id"],
                    "run_count": raw["run_count"],
                    "pass_at_4": row["pass_at_4"],
                    "passed_attempts": row["passed_attempts"],
                    "attempted_tasks": row["attempted_tasks"],
                    "ci_method": raw["ci_method"],
                    "leaderboard_generated_at": raw["generated_at"],
                },
                number_of_tasks=int(str(raw["task_count"])),
                number_of_trials=int(str(row["attempted_tasks"])),
                sample_count=int(str(row["attempted_tasks"])),
                pass_at_k=1,
                uncertainty=MeasurementUncertainty(
                    kind=UncertaintyKind.CONFIDENCE_INTERVAL,
                    lower=float(cast(float, row["ci_lower"])) * 100.0,
                    upper=float(cast(float, row["ci_upper"])) * 100.0,
                    confidence_level=0.95,
                    source_fields=("ci_lower", "ci_upper", "ci_method"),
                    notes=str(raw["ci_method"]),
                ),
                metric_definition="DeepSWE v1.1 task resolution rate in percent",
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=benchmark_version,
                harness_version="pier-mini-swe-agent-deepswe-v1.1",
                evaluator="Datacurve",
                harness_owner="Datacurve",
                run_executor="Datacurve",
                raw_artifact_available=False,
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="deepswe-v1.1",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
            )
        )
        efficiency.append(
            EfficiencyMeasurement(
                record_id=identifier(f"deepswe-harness-resources-{match.canonical_model_id}-{as_of}"),
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                workload="deepswe-v1.1",
                workload_category=WorkloadCategory.CODING,
                cohort_key=identifier(f"deepswe-v1.1-{as_of}"),
                evaluation_date=as_of,
                attempts=int(str(row["attempted_tasks"])),
                success_rate=float(cast(float, row["pass_rate"])),
                mean_input_tokens=float(cast(float, row["mean_input_tokens"])),
                mean_output_tokens=float(cast(float, row["mean_output_tokens"])),
                mean_agent_steps=float(cast(float, row["mean_agent_steps"])),
                aggregation_statistic=AggregationStatistic.ARITHMETIC_MEAN,
                metric_definition=(
                    "Arithmetic mean input tokens, output tokens, and mini-swe-agent steps per "
                    "attempt across the published DeepSWE leaderboard run set"
                ),
                signal_role=SignalRole.EFFICIENCY,
                scoring_disposition=ScoringDisposition.SCORED,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=benchmark_version,
                harness_version="pier-mini-swe-agent-deepswe-v1.1",
                evaluator="Datacurve",
                harness_owner="Datacurve",
                run_executor="Datacurve",
                raw_artifact_available=False,
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="deepswe-v1.1-resources",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
            )
        )
        efficiency.append(
            EfficiencyMeasurement(
                record_id=identifier(
                    f"deepswe-endpoint-resources-{match.canonical_model_id}-{as_of}"
                ),
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                workload="deepswe-v1.1",
                workload_category=WorkloadCategory.CODING,
                cohort_key=identifier(f"deepswe-v1.1-{as_of}"),
                evaluation_date=as_of,
                attempts=int(str(row["attempted_tasks"])),
                success_rate=float(cast(float, row["pass_rate"])),
                mean_wall_seconds=float(cast(float, row["mean_duration_seconds"])),
                mean_cost_per_attempt=float(cast(float, row["mean_cost_usd"])),
                aggregation_statistic=AggregationStatistic.ARITHMETIC_MEAN,
                metric_definition=(
                    "Arithmetic mean wall duration and dollar cost per attempt from the published "
                    "DeepSWE leaderboard; retained diagnostically until deployment identity is "
                    "verified"
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
                raw_artifact_available=False,
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="deepswe-v1.1-endpoint-resources",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="deepswe-reviewed-facts-v1",
        benchmarks=tuple(benchmarks),
        efficiency=tuple(efficiency),
        rejections=tuple(rejected),
        diagnostics=(
            "DeepSWE wall time and dollar cost remain diagnostic pending deployment identity",
        ),
    )


def adapt_lab_release_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    """Adapt manually reviewed facts from one official lab artifact.

    Prices remain descriptive inputs. Release claims are typed diagnostic records and never
    become benchmark measurements through this adapter.
    """
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    prices: list[PricingRecord] = []
    claims: list[ReleaseClaim] = []
    rejected: list[AdapterRejection] = []

    def matched(source_model_id: str) -> ModelCrosswalkEntry | None:
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            return None
        return match

    def optional_float(row: dict[str, object], key: str) -> float | None:
        value = row.get(key)
        return None if value is None else float(cast(float, value))

    for row_value in cast(list[object], raw.get("pricing", [])):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        match = matched(source_model_id)
        if match is None or match.canonical_model_id is None:
            continue
        effective = date.fromisoformat(str(row["effective_date"]))
        prices.append(
            PricingRecord(
                record_id=identifier(f"{source_id}-pricing-{match.canonical_model_id}-{effective}"),
                model_id=match.canonical_model_id,
                effective_date=effective,
                input_per_million=optional_float(row, "input_per_million"),
                cached_input_per_million=optional_float(row, "cached_input_per_million"),
                output_per_million=optional_float(row, "output_per_million"),
                cache_write_per_million=optional_float(row, "cache_write_per_million"),
                cache_write_1h_per_million=optional_float(row, "cache_write_1h_per_million"),
                long_context_surcharge=cast(
                    dict[str, float], row.get("long_context_surcharge", {})
                ),
                tool_costs=cast(dict[str, float], row.get("tool_costs", {})),
                source=source,
                result_type=ResultType.VENDOR,
                metric_definition=str(row["metric_definition"]),
                evaluator=source.organization,
                raw_artifact_available=True,
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                source_model_id=source_model_id,
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                record_status=RecordStatus.DIAGNOSTIC_ONLY,
                signal_role=SignalRole.ECONOMICS,
                scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
                notes=(
                    "Token tariff only; it cannot establish task cost without compatible "
                    "task-level resource measurements."
                ),
            )
        )

    for row_value in cast(list[object], raw.get("claims", [])):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        match = matched(source_model_id)
        if match is None or match.canonical_model_id is None:
            continue
        evaluated = date.fromisoformat(str(row["evaluation_date"]))
        claims.append(
            ReleaseClaim(
                record_id=identifier(
                    f"{source_id}-claim-{row['benchmark_id']}-{match.canonical_model_id}-{evaluated}"
                ),
                claim_text=str(row["claim_text"]),
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                benchmark_id=identifier(str(row["benchmark_id"])),
                value=float(cast(float, row["value"])),
                unit=Unit(str(row["unit"])),
                direction=Direction(str(row["direction"])),
                cohort_key=identifier(str(row["cohort_key"])),
                evaluation_date=evaluated,
                source=source,
                result_type=ResultType.VENDOR,
                benchmark_version=identifier(str(row["benchmark_id"])),
                harness_version=str(row["cohort_key"]),
                metric_definition="Literal numeric result published in an official lab release",
                evaluator=source.organization,
                raw_artifact_available=True,
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                record_status=RecordStatus.DIAGNOSTIC_ONLY,
                signal_role=SignalRole.REFERENCE,
                scoring_disposition=ScoringDisposition.DIAGNOSTIC_ONLY,
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="lab-release-reviewed-facts-v1",
        pricing=tuple(prices),
        release_claims=tuple(claims),
        rejections=tuple(rejected),
        diagnostics=(
            "Pricing cannot establish workload economics without compatible resource usage",
            "Vendor release claims are diagnostic and require exact independent reproduction",
        ),
    )
