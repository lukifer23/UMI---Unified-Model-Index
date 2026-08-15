from __future__ import annotations

import math
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
    benchmarks: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []
    benchmark_raw = cast(dict[str, object] | None, raw.get("benchmark"))
    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        if benchmark_raw is not None:
            source_rate = float(cast(float, row["source_value_rate"]))
            benchmarks.append(
                BenchmarkMeasurement(
                    record_id=identifier(
                        f"aa-{benchmark_raw['benchmark_id']}-{match.canonical_model_id}-{as_of}"
                    ),
                    benchmark_id=identifier(str(benchmark_raw["benchmark_id"])),
                    model_id=match.canonical_model_id,
                    source_model_id=source_model_id,
                    value=source_rate * 100.0,
                    cohort_key=identifier(str(benchmark_raw["cohort_key"])),
                    measurement_as_of_date=as_of,
                    source=source,
                    result_type=ResultType.INDEPENDENT,
                    benchmark_version=str(benchmark_raw["benchmark_version"]),
                    harness_version=str(benchmark_raw["harness_version"]),
                    metric_definition=str(benchmark_raw["metric_definition"]),
                    evaluator=str(benchmark_raw["evaluator"]),
                    harness_owner=str(benchmark_raw["harness_owner"]),
                    run_executor=str(benchmark_raw["run_executor"]),
                    tools_enabled=bool(benchmark_raw["tools_enabled"]),
                    capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                    reproducible=bool(benchmark_raw["reproducible"]),
                    source_artifact_id=artifact_id,
                    source_registry_snapshot_id=artifact_id,
                    crosswalk_entry_id=match.id,
                    signal_id="hle",
                    configuration_verification=ConfigurationVerification(
                        model_label_exact=True,
                        release_label_exact=True,
                        effort_label_exact=True,
                        fallback_absent=True,
                    ),
                    record_status=RecordStatus.READY,
                    signal_role=SignalRole.TASK,
                    scoring_disposition=ScoringDisposition.SCORED,
                    evaluation_settings={
                        **cast(dict[str, object], benchmark_raw["evaluation_settings"]),
                        "source_value_rate": source_rate,
                    },
                    number_of_tasks=int(cast(int, benchmark_raw["number_of_tasks"])),
                    number_of_trials=int(cast(int, benchmark_raw["number_of_trials"])),
                    sample_count=int(cast(int, benchmark_raw["number_of_tasks"])),
                    pass_at_k=int(cast(int, benchmark_raw["pass_at_k"])),
                    notes=(
                        "Reviewed public-page fact; source rate multiplied by 100 for the "
                        "configured percent unit. Access date is not an evaluation date."
                    ),
                )
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
        adapter_id="aa-reviewed-facts-v2" if benchmark_raw is not None else "aa-reviewed-facts-v1",
        benchmarks=tuple(benchmarks),
        external_indexes=tuple(records),
        rejections=tuple(rejected),
    )


def adapt_cursorbench_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    """Adapt reviewed CursorBench facts without promoting operational summaries to scores."""
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    as_of = date.fromisoformat(str(raw["as_of"]))
    benchmark = cast(dict[str, object], raw["benchmark"])
    identity_review = cast(dict[str, object], raw["identity_review"])
    fable_review = cast(dict[str, object], identity_review["fable_fallback"])
    fable_finding = str(fable_review["finding"])
    if not str(fable_review["source_url"]).startswith("https://"):
        raise ValueError("CursorBench Fable fallback review requires an HTTPS source URL")
    benchmarks: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []

    def finite_nonnegative(row: dict[str, object], key: str) -> float:
        value = float(cast(float, row[key]))
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"CursorBench {key} must be finite and nonnegative")
        return value

    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        score = finite_nonnegative(row, "score_percent")
        if score > 100:
            raise ValueError("CursorBench score_percent must not exceed 100")
        cost = finite_nonnegative(row, "avg_cost_per_task_usd")
        tokens = finite_nonnegative(row, "tokens_per_task")
        steps = finite_nonnegative(row, "steps_per_task")
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(
                    source_row_id=source_model_id,
                    reason=fable_finding
                    if source_model_id == "Fable 5 Max"
                    else "no exact crosswalk",
                )
            )
            continue
        benchmarks.append(
            BenchmarkMeasurement(
                record_id=identifier(f"cursorbench-3.2-{match.canonical_model_id}-{as_of}"),
                benchmark_id=identifier(str(benchmark["benchmark_id"])),
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=score,
                cohort_key=identifier(str(benchmark["cohort_key"])),
                measurement_as_of_date=as_of,
                evaluation_settings={
                    **cast(dict[str, object], benchmark["evaluation_settings"]),
                    "avg_cost_per_task_usd": cost,
                    "tokens_per_task": int(tokens),
                    "steps_per_task": int(steps),
                },
                metric_definition=str(benchmark["metric_definition"]),
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=str(benchmark["benchmark_version"]),
                harness_version=str(benchmark["harness_version"]),
                evaluator=str(benchmark["evaluator"]),
                harness_owner=str(benchmark["harness_owner"]),
                run_executor=str(benchmark["run_executor"]),
                tools_enabled=bool(benchmark["tools_enabled"]),
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                reproducible=bool(benchmark["reproducible"]),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="cursorbench-3.2",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                record_status=RecordStatus.READY,
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                notes=(
                    "Capability score only. Published task cost, token, and step summaries are "
                    "retained in evaluation_settings but excluded from Efficiency and Economics."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="cursorbench-reviewed-facts-v1",
        benchmarks=tuple(benchmarks),
        rejections=tuple(rejected),
        diagnostics=(
            "CursorBench operational summaries remain diagnostic without compatible success "
            "and deployment identity",
            f"Fable 5 Max rejected: {fable_finding}",
        ),
    )


def adapt_aa_gdpval_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    """Adapt a frozen GDPval-AA v2 public fact extract into task evidence."""
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    as_of = date.fromisoformat(str(raw["as_of"]))
    benchmark = cast(dict[str, object], raw["benchmark"])
    benchmarks: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []

    def finite(row: dict[str, object], key: str) -> float:
        value = float(cast(float, row[key]))
        if not math.isfinite(value):
            raise ValueError(f"GDPval-AA v2 {key} must be finite")
        return value

    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        elo = finite(row, "elo")
        lower = finite(row, "ci_lower")
        upper = finite(row, "ci_upper")
        if not lower <= elo <= upper:
            raise ValueError("GDPval-AA v2 confidence interval must contain the Elo estimate")
        turns = finite(row, "average_turns_per_task")
        if turns < 0:
            raise ValueError("GDPval-AA v2 average_turns_per_task must be nonnegative")
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue

        operational: dict[str, object] = {"average_turns_per_task": turns}
        for key in ("output_answer_tokens_per_task", "output_reasoning_tokens_per_task"):
            if key in row:
                value = finite(row, key)
                if value < 0:
                    raise ValueError(f"GDPval-AA v2 {key} must be nonnegative")
                operational[key] = value
        if "calculated_cost_components_usd" in row:
            components = cast(dict[str, object], row["calculated_cost_components_usd"])
            checked_components: dict[str, float] = {}
            for key, raw_value in components.items():
                value = float(cast(float, raw_value))
                if not math.isfinite(value) or value < 0:
                    raise ValueError(
                        "GDPval-AA v2 calculated cost component "
                        f"{key} must be finite and nonnegative"
                    )
                checked_components[str(key)] = value
            operational["calculated_cost_components_usd"] = checked_components

        benchmarks.append(
            BenchmarkMeasurement(
                record_id=identifier(f"aa-gdpval-v2-{match.canonical_model_id}-{as_of}"),
                benchmark_id=identifier(str(benchmark["benchmark_id"])),
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=elo,
                cohort_key=identifier(str(benchmark["cohort_key"])),
                measurement_as_of_date=as_of,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=str(benchmark["benchmark_version"]),
                harness_version=str(benchmark["harness_version"]),
                metric_definition=str(benchmark["metric_definition"]),
                evaluator=str(benchmark["evaluator"]),
                harness_owner=str(benchmark["harness_owner"]),
                run_executor=str(benchmark["run_executor"]),
                tools_enabled=bool(benchmark["tools_enabled"]),
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                reproducible=bool(benchmark["reproducible"]),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="gdpval-aa-v2",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                record_status=RecordStatus.READY,
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                evaluation_settings={
                    **cast(dict[str, object], benchmark["evaluation_settings"]),
                    **operational,
                },
                number_of_tasks=int(cast(int, benchmark["number_of_tasks"])),
                number_of_trials=int(cast(int, benchmark["number_of_trials"])),
                sample_count=int(cast(int, benchmark["number_of_tasks"])),
                uncertainty=MeasurementUncertainty(
                    kind=UncertaintyKind.CONFIDENCE_INTERVAL,
                    lower=lower,
                    upper=upper,
                    confidence_level=0.95,
                    source_fields=("ci_lower", "ci_upper", "uncertainty_method"),
                    notes=str(benchmark["uncertainty_method"]),
                ),
                notes=(
                    "Reviewed public-page Elo snapshot. Per-task operational summaries are "
                    "diagnostic evaluation settings and do not enter Efficiency or Economics."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="aa-gdpval-reviewed-facts-v1",
        benchmarks=tuple(benchmarks),
        rejections=tuple(rejected),
        diagnostics=(
            "GDPval-AA operational summaries remain diagnostic because Elo is not a binary "
            "success denominator",
        ),
    )


def _adapt_aa_pass_rate_facts(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    record_prefix: str,
    adapter_id: str,
    diagnostic: str,
) -> AdaptationResult:
    """Adapt one reviewed AA pass-rate cohort without promoting operational summaries."""
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    as_of = date.fromisoformat(str(raw["as_of"]))
    benchmark = cast(dict[str, object], raw["benchmark"])
    benchmarks: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []

    def finite_nonnegative(row: dict[str, object], key: str) -> float:
        value = float(cast(float, row[key]))
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{benchmark['benchmark_id']} {key} must be finite and nonnegative")
        return value

    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        source_rate = finite_nonnegative(row, "source_value_rate")
        if source_rate > 1:
            raise ValueError(f"{benchmark['benchmark_id']} source_value_rate must not exceed 1")

        operational: dict[str, object] = {}
        for key in (
            "output_answer_tokens_per_task",
            "output_reasoning_tokens_per_task",
            "weighted_decode_time_per_task",
        ):
            if key in row:
                operational[key] = finite_nonnegative(row, key)
        if "calculated_cost_components_usd" in row:
            components = cast(dict[str, object], row["calculated_cost_components_usd"])
            operational["calculated_cost_components_usd"] = {
                str(key): finite_nonnegative({str(key): value}, str(key))
                for key, value in components.items()
            }

        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        benchmarks.append(
            BenchmarkMeasurement(
                record_id=identifier(f"{record_prefix}-{match.canonical_model_id}-{as_of}"),
                benchmark_id=identifier(str(benchmark["benchmark_id"])),
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=source_rate * 100.0,
                cohort_key=identifier(str(benchmark["cohort_key"])),
                measurement_as_of_date=as_of,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=str(benchmark["benchmark_version"]),
                harness_version=str(benchmark["harness_version"]),
                metric_definition=str(benchmark["metric_definition"]),
                evaluator=str(benchmark["evaluator"]),
                harness_owner=str(benchmark["harness_owner"]),
                run_executor=str(benchmark["run_executor"]),
                tools_enabled=bool(benchmark["tools_enabled"]),
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                reproducible=bool(benchmark["reproducible"]),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id=identifier(str(benchmark["benchmark_id"])),
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                record_status=RecordStatus.READY,
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                evaluation_settings={
                    **cast(dict[str, object], benchmark["evaluation_settings"]),
                    "repeats_per_task": int(cast(int, benchmark["repeats_per_task"])),
                    "source_value_rate": source_rate,
                    **operational,
                },
                number_of_tasks=int(cast(int, benchmark["number_of_tasks"])),
                number_of_trials=int(cast(int, benchmark["number_of_trials"])),
                sample_count=int(cast(int, benchmark["number_of_trials"])),
                pass_at_k=int(cast(int, benchmark["pass_at_k"])),
                notes=(
                    "Capability pass rate only. Incomplete operational summaries are retained "
                    "diagnostically and do not enter Efficiency or Economics."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id=adapter_id,
        benchmarks=tuple(benchmarks),
        rejections=tuple(rejected),
        diagnostics=(diagnostic,),
    )


def adapt_aa_tau3_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    """Adapt a frozen τ³-Banking public fact extract into task evidence."""
    return _adapt_aa_pass_rate_facts(
        path,
        crosswalk,
        record_prefix="aa-tau3-banking",
        adapter_id="aa-tau3-reviewed-facts-v1",
        diagnostic=(
            "τ³-Banking operational summaries remain diagnostic because coverage, billing, "
            "and decode-time unit semantics are incomplete"
        ),
    )


def adapt_aa_lcr_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    """Adapt a frozen AA-LCR public fact extract into long-context task evidence."""
    return _adapt_aa_pass_rate_facts(
        path,
        crosswalk,
        record_prefix="aa-lcr",
        adapter_id="aa-lcr-reviewed-facts-v1",
        diagnostic=(
            "AA-LCR operational summaries remain diagnostic because token accounting is "
            "provider-specific and operational coverage is incomplete"
        ),
    )


def adapt_aa_omniscience_facts(path: str | Path, crosswalk: ModelCrosswalk) -> AdaptationResult:
    """Adapt one frozen AA-Omniscience cohort and verify its published decomposition."""
    raw = load_yaml(path)
    source_id = str(raw["source_id"])
    artifact_id = str(raw["artifact_id"])
    source = Source.model_validate(raw["source"])
    as_of = date.fromisoformat(str(raw["as_of"]))
    benchmark = cast(dict[str, object], raw["benchmark"])
    task_count = int(cast(int, benchmark["number_of_tasks"]))
    benchmarks: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []

    def finite(value: object, field: str) -> float:
        parsed = float(cast(float, value))
        if not math.isfinite(parsed):
            raise ValueError(f"AA-Omniscience {field} must be finite")
        return parsed

    def rate(value: object, field: str) -> float:
        parsed = finite(value, field)
        if not 0 <= parsed <= 1:
            raise ValueError(f"AA-Omniscience {field} must be between 0 and 1")
        return parsed

    for row_value in cast(list[object], raw["rows"]):
        row = cast(dict[str, object], row_value)
        source_model_id = str(row["source_model_id"])
        counts = {
            key: int(cast(int, row[key]))
            for key in (
                "num_correct",
                "num_incorrect",
                "num_partial_answer",
                "num_not_attempted",
            )
        }
        if any(value < 0 for value in counts.values()) or sum(counts.values()) != task_count:
            raise ValueError("AA-Omniscience answer counts must be nonnegative and sum to tasks")

        index_value = finite(row["omniscience_index"], "omniscience_index")
        if not -100 <= index_value <= 100:
            raise ValueError("AA-Omniscience omniscience_index must be between -100 and 100")
        expected_index = 100.0 * (counts["num_correct"] - counts["num_incorrect"]) / task_count
        if not math.isclose(index_value, expected_index, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("AA-Omniscience index does not match answer counts")

        accuracy = rate(row["accuracy_rate"], "accuracy_rate")
        attempt = rate(row["attempt_rate"], "attempt_rate")
        hallucination = rate(row["hallucination_rate"], "hallucination_rate")
        expected_accuracy = counts["num_correct"] / task_count
        expected_attempt = 1.0 - (counts["num_not_attempted"] / task_count)
        noncorrect = task_count - counts["num_correct"]
        expected_hallucination = counts["num_incorrect"] / noncorrect
        for observed, expected, field in (
            (accuracy, expected_accuracy, "accuracy_rate"),
            (attempt, expected_attempt, "attempt_rate"),
            (hallucination, expected_hallucination, "hallucination_rate"),
        ):
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"AA-Omniscience {field} does not match answer counts")

        token_counts = {
            str(key): int(cast(int, value))
            for key, value in cast(dict[str, object], row["token_counts"]).items()
        }
        if any(value < 0 for value in token_counts.values()) or token_counts["output"] != (
            token_counts["answer"] + token_counts["reasoning"]
        ):
            raise ValueError("AA-Omniscience token counts must be nonnegative and reconcile")
        costs = {
            str(key): finite(value, f"calculated_cost_usd.{key}")
            for key, value in cast(dict[str, object], row["calculated_cost_usd"]).items()
        }
        if (
            any(value < 0 for value in costs.values())
            or not math.isclose(
                costs["output"], costs["answer"] + costs["reasoning"], abs_tol=1e-12
            )
            or not math.isclose(costs["total"], costs["input"] + costs["output"], abs_tol=1e-12)
        ):
            raise ValueError("AA-Omniscience calculated costs must be nonnegative and reconcile")
        upstream_time = finite(row["upstream_eval_time_per_task"], "eval_time_per_task")
        if upstream_time < 0:
            raise ValueError("AA-Omniscience eval_time_per_task must be nonnegative")

        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        benchmarks.append(
            BenchmarkMeasurement(
                record_id=identifier(f"aa-omniscience-{match.canonical_model_id}-{as_of}"),
                benchmark_id="aa-omniscience",
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=index_value,
                cohort_key=identifier(str(benchmark["cohort_key"])),
                measurement_as_of_date=as_of,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version=str(benchmark["benchmark_version"]),
                harness_version=str(benchmark["harness_version"]),
                metric_definition=str(benchmark["metric_definition"]),
                evaluator=str(benchmark["evaluator"]),
                harness_owner=str(benchmark["harness_owner"]),
                run_executor=str(benchmark["run_executor"]),
                tools_enabled=bool(benchmark["tools_enabled"]),
                capture_type=ArtifactCaptureType.REVIEWED_FACT_EXTRACT,
                reproducible=bool(benchmark["reproducible"]),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="aa-omniscience",
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                record_status=RecordStatus.READY,
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                evaluation_settings={
                    **cast(dict[str, object], benchmark["evaluation_settings"]),
                    "answer_counts": counts,
                    "accuracy_rate": accuracy,
                    "attempt_rate": attempt,
                    "hallucination_rate": hallucination,
                    "token_counts": token_counts,
                    "calculated_cost_usd": costs,
                    "upstream_eval_time_per_task": upstream_time,
                    "performance_data_source": str(row["performance_data_source"]),
                },
                number_of_tasks=task_count,
                number_of_trials=int(cast(int, benchmark["number_of_trials"])),
                sample_count=task_count,
                notes=(
                    "The published Omniscience Index is the sole scored signal. Accuracy, "
                    "hallucination, tokens, calculated cost, and time remain diagnostic."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="aa-omniscience-reviewed-facts-v1",
        benchmarks=tuple(benchmarks),
        rejections=tuple(rejected),
        diagnostics=(
            "AA-Omniscience component and operational facts are retained diagnostically; "
            "only the source-defined reliability Index scores",
        ),
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
                record_id=identifier(
                    f"deepswe-harness-resources-{match.canonical_model_id}-{as_of}"
                ),
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
