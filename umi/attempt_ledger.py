from __future__ import annotations

import hashlib
import json
from math import fsum
from pathlib import Path
from typing import Any, cast

import yaml

from umi.schemas import (
    AggregationStatistic,
    AttemptLedger,
    AttemptLedgerAggregation,
    AttemptMetricSummary,
    BillingEvidenceKind,
    CostBasis,
    EfficiencyMeasurement,
    EfficiencyObservationCounts,
    RecordStatus,
    ResultType,
    ScoringDisposition,
    SignalRole,
    TaskEconomicsMeasurement,
)

_EFFICIENCY_FIELDS = {
    "input_tokens": ("mean_input_tokens", "input_tokens"),
    "output_tokens": ("mean_output_tokens", "output_tokens"),
    "reasoning_tokens": ("mean_reasoning_tokens", "reasoning_tokens"),
    "cache_read_tokens": ("mean_cached_tokens", "cached_tokens"),
    "turns": ("mean_turns", "turns"),
    "agent_steps": ("mean_agent_steps", "agent_steps"),
    "wall_seconds": ("mean_wall_seconds", "wall_seconds"),
    "tool_calls": ("mean_tool_calls", "tool_calls"),
}

_SUMMARY_FIELDS = (
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "turns",
    "agent_steps",
    "wall_seconds",
    "tool_calls",
    "retry_count",
    "observed_cost_usd",
)


def load_attempt_ledger(path: str | Path) -> AttemptLedger:
    source_path = Path(path)
    with source_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{source_path} must contain one attempt-ledger mapping")
    return AttemptLedger.model_validate(raw)


def _ordered_ledger_payload(ledger: AttemptLedger) -> dict[str, Any]:
    payload = ledger.model_dump(mode="json")
    payload["attempts"] = sorted(
        cast(list[dict[str, Any]], payload["attempts"]),
        key=lambda item: (str(item["task_id"]), str(item["attempt_id"])),
    )
    return payload


def attempt_ledger_fingerprint(ledger: AttemptLedger) -> str:
    rendered = json.dumps(
        _ordered_ledger_payload(ledger),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _metric_summaries(ledger: AttemptLedger) -> tuple[AttemptMetricSummary, ...]:
    attempts = sorted(ledger.attempts, key=lambda item: (item.task_id, item.attempt_id))
    output: list[AttemptMetricSummary] = []
    for field in _SUMMARY_FIELDS:
        values = [float(value) for item in attempts if (value := getattr(item, field)) is not None]
        if values:
            output.append(
                AttemptMetricSummary(
                    metric=field,
                    observation_count=len(values),
                    mean=fsum(values) / len(values),
                )
            )
    return tuple(output)


def _provenance(ledger: AttemptLedger) -> dict[str, object]:
    deployment = ledger.deployment
    return {
        "source": ledger.source,
        "model_release_date": ledger.model_release_date,
        "measurement_as_of_date": ledger.measurement_as_of_date,
        "result_type": ResultType.DERIVED,
        "benchmark_version": ledger.workload_version,
        "harness_version": ledger.harness_version,
        "metric_definition": (
            "Deterministic arithmetic means over one frozen, exact-deployment attempt ledger"
        ),
        "tools_enabled": ledger.tools_enabled,
        "evaluator": ledger.evaluator,
        "harness_owner": ledger.harness_owner,
        "run_executor": ledger.run_executor,
        "capture_type": ledger.capture_type,
        "reproducible": True,
        "configuration_verification": deployment.configuration_verification,
        "source_artifact_id": ledger.source_artifact_id,
        "source_registry_snapshot_id": ledger.source_artifact_id,
        "crosswalk_entry_id": ledger.crosswalk_entry_id,
        "source_model_id": deployment.source_model_id,
        "provider_snapshot_id": deployment.provider_snapshot_id,
        "serving_provider": deployment.serving_provider,
        "endpoint_id": deployment.endpoint_id,
        "service_tier": deployment.service_tier,
    }


def _efficiency_records(
    ledger: AttemptLedger,
    summaries: tuple[AttemptMetricSummary, ...],
    successful_attempts: int,
) -> tuple[EfficiencyMeasurement, ...]:
    summary_by_metric = {item.metric: item for item in summaries}
    complete_means: dict[str, float] = {}
    complete_counts: dict[str, int] = {}
    partial_means: dict[str, float] = {}
    partial_counts: dict[str, int] = {}
    attempt_count = len(ledger.attempts)
    for source_field, (mean_field, count_field) in _EFFICIENCY_FIELDS.items():
        summary = summary_by_metric.get(source_field)
        if summary is None:
            continue
        means = complete_means if summary.observation_count == attempt_count else partial_means
        counts = complete_counts if summary.observation_count == attempt_count else partial_counts
        means[mean_field] = summary.mean
        counts[count_field] = summary.observation_count

    common = {
        **_provenance(ledger),
        "model_id": ledger.deployment.model_id,
        "workload": ledger.workload,
        "workload_category": ledger.workload_category,
        "interaction_profile": ledger.interaction_profile,
        "operational_profile_id": ledger.operational_profile_id,
        "success_definition_id": ledger.success_definition_id,
        "success_definition": ledger.success_definition,
        "cohort_key": ledger.cohort_key,
        "evaluation_date": ledger.evaluation_date,
        "attempts": attempt_count,
        "successful_attempts": successful_attempts,
        "success_rate": successful_attempts / attempt_count,
        "aggregation_statistic": AggregationStatistic.ARITHMETIC_MEAN,
        "signal_id": ledger.signal_id,
        "signal_role": SignalRole.EFFICIENCY,
    }
    output: list[EfficiencyMeasurement] = []
    if complete_means:
        is_ready = ledger.record_status == RecordStatus.READY
        output.append(
            EfficiencyMeasurement.model_validate(
                {
                    **common,
                    **complete_means,
                    "record_id": f"{ledger.ledger_id}-complete-resources",
                    "observation_counts": EfficiencyObservationCounts.model_validate(
                        complete_counts
                    ),
                    "record_status": ledger.record_status,
                    "scoring_disposition": (
                        ScoringDisposition.SCORED
                        if is_ready
                        else ScoringDisposition.DIAGNOSTIC_ONLY
                    ),
                    "notes": (
                        "Complete physical resource observations from every attempt; cache-read "
                        "tokens populate mean_cached_tokens"
                    ),
                }
            )
        )
    if partial_means:
        output.append(
            EfficiencyMeasurement.model_validate(
                {
                    **common,
                    **partial_means,
                    "record_id": f"{ledger.ledger_id}-partial-resources",
                    "observation_counts": EfficiencyObservationCounts.model_validate(
                        partial_counts
                    ),
                    "record_status": RecordStatus.DIAGNOSTIC_ONLY,
                    "scoring_disposition": ScoringDisposition.DIAGNOSTIC_ONLY,
                    "notes": "Partial physical observations retained with their own denominators",
                }
            )
        )
    return tuple(output)


def _economics_records(
    ledger: AttemptLedger,
    successful_attempts: int,
) -> tuple[tuple[TaskEconomicsMeasurement, ...], tuple[str, ...]]:
    costs = [attempt.observed_cost_usd for attempt in ledger.attempts]
    observed_costs = [float(value) for value in costs if value is not None]
    if not observed_costs:
        return (), ("no observed attempt costs",)
    if len(observed_costs) != len(ledger.attempts):
        return (), (
            f"cost observed on {len(observed_costs)} of {len(ledger.attempts)} attempts",
        )
    if successful_attempts == 0:
        return (), ("zero successes; no finite observed cost per successful task serialized",)
    if ledger.record_status != RecordStatus.READY:
        return (), ("attempt ledger is not ready for observed Economics",)
    if any(
        attempt.billing_evidence != BillingEvidenceKind.PROVIDER_BILLING_RECORD
        for attempt in ledger.attempts
    ):
        return (), ("cost evidence is not provider-billing-record complete",)

    total_cost = fsum(observed_costs)
    record = TaskEconomicsMeasurement.model_validate(
        {
            **_provenance(ledger),
            "record_id": f"{ledger.ledger_id}-observed-economics",
            "model_id": ledger.deployment.model_id,
            "workload": ledger.workload,
            "workload_category": ledger.workload_category,
            "interaction_profile": ledger.interaction_profile,
            "operational_profile_id": ledger.operational_profile_id,
            "success_definition_id": ledger.success_definition_id,
            "success_definition": ledger.success_definition,
            "cohort_key": ledger.cohort_key,
            "evaluation_date": ledger.evaluation_date,
            "cost_basis": CostBasis.SUCCESSFUL_TASK,
            "mean_cost_usd": total_cost / successful_attempts,
            "number_of_tasks": len({attempt.task_id for attempt in ledger.attempts}),
            "attempts": len(ledger.attempts),
            "successful_attempts": successful_attempts,
            "cost_observation_count": len(observed_costs),
            "total_observed_cost_usd": total_cost,
            "billing_evidence": BillingEvidenceKind.PROVIDER_BILLING_RECORD,
            "aggregation_statistic": AggregationStatistic.ARITHMETIC_MEAN,
            "record_status": RecordStatus.READY,
            "signal_id": ledger.signal_id,
            "signal_role": SignalRole.ECONOMICS,
            "scoring_disposition": ScoringDisposition.SCORED,
            "metric_definition": (
                "Total provider-billed attempt cost divided by successful attempts in one "
                "exact-deployment workload cohort"
            ),
        }
    )
    return (record,), ()


def aggregate_attempt_ledger(ledger: AttemptLedger) -> AttemptLedgerAggregation:
    attempts = tuple(sorted(ledger.attempts, key=lambda item: (item.task_id, item.attempt_id)))
    successful_attempts = sum(attempt.success for attempt in attempts)
    summaries = _metric_summaries(ledger)
    efficiency = _efficiency_records(ledger, summaries, successful_attempts)
    economics, economics_diagnostics = _economics_records(ledger, successful_attempts)
    diagnostics = list(economics_diagnostics)
    cache_write = next((item for item in summaries if item.metric == "cache_write_tokens"), None)
    if cache_write is not None:
        diagnostics.append(
            "cache-write tokens retained as a physical diagnostic; no Efficiency weight exists"
        )
    partial = [
        item.metric for item in summaries if item.observation_count != len(attempts)
    ]
    if partial:
        diagnostics.append("partial metric denominators: " + ", ".join(sorted(partial)))
    return AttemptLedgerAggregation(
        ledger_id=ledger.ledger_id,
        fingerprint=attempt_ledger_fingerprint(ledger),
        task_count=len({attempt.task_id for attempt in attempts}),
        attempt_count=len(attempts),
        successful_attempts=successful_attempts,
        success_rate=successful_attempts / len(attempts),
        metric_summaries=summaries,
        efficiency_records=efficiency,
        economics_records=economics,
        diagnostics=tuple(sorted(set(diagnostics))),
    )
