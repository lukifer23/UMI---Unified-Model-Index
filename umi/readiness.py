from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from umi.loading import Dataset
from umi.schemas import (
    AggregationStatistic,
    BenchmarkMeasurement,
    BillingEvidenceKind,
    CostBasis,
    EfficiencyMeasurement,
    ExternalIndexMeasurement,
    IdentityAssurance,
    ModelConfiguration,
    Provenance,
    RecordStatus,
    ScoringDisposition,
    TaskEconomicsMeasurement,
)

ScoredRecord = (
    BenchmarkMeasurement
    | EfficiencyMeasurement
    | TaskEconomicsMeasurement
    | ExternalIndexMeasurement
)

IDENTITY_ASSURANCE_ORDER = {
    IdentityAssurance.UNKNOWN: 0,
    IdentityAssurance.INFERRED: 1,
    IdentityAssurance.LABEL_EXACT: 2,
    IdentityAssurance.STRONGLY_SUPPORTED: 3,
    IdentityAssurance.VERIFIED: 4,
}


def evidence_date(record: Provenance) -> date | None:
    """Return the best truthful date for freshness without relabeling it as an eval run date."""
    return (
        getattr(record, "evaluation_date", None)
        or record.measurement_as_of_date
        or record.leaderboard_publish_date
        or record.source_published_date
    )


def readiness_failures(record: ScoredRecord, model: ModelConfiguration) -> tuple[str, ...]:
    if record.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY:
        return ("signal policy is diagnostic-only",)
    if record.record_status == RecordStatus.INVALID:
        return ("record status is invalid",)
    if record.record_status == RecordStatus.DIAGNOSTIC_ONLY:
        return ("record is diagnostic-only",)
    if model.synthetic or record.record_status == RecordStatus.SYNTHETIC:
        if not model.synthetic or record.record_status not in {
            RecordStatus.SYNTHETIC,
            RecordStatus.READY,
        }:
            return ("synthetic status does not match the model",)
        return ()

    failures: list[str] = []
    if record.record_status != RecordStatus.READY:
        failures.append("record status is not ready")
    if isinstance(record, (EfficiencyMeasurement, TaskEconomicsMeasurement)):
        if record.interaction_profile is None:
            failures.append("interaction profile is missing")
        if record.operational_profile_id is None:
            failures.append("operational profile ID is missing")
        if record.success_definition_id is None or not record.success_definition:
            failures.append("success definition identity is missing")
    if (
        isinstance(record, EfficiencyMeasurement)
        and record.aggregation_statistic == AggregationStatistic.ARITHMETIC_MEAN
    ):
        if record.successful_attempts is None:
            failures.append("successful attempt count is missing")
        count_pairs = (
            ("mean_input_tokens", "input_tokens"),
            ("mean_output_tokens", "output_tokens"),
            ("mean_reasoning_tokens", "reasoning_tokens"),
            ("mean_cached_tokens", "cached_tokens"),
            ("mean_total_tokens", "total_tokens"),
            ("mean_turns", "turns"),
            ("mean_agent_steps", "agent_steps"),
            ("mean_wall_seconds", "wall_seconds"),
            ("mean_tool_calls", "tool_calls"),
            ("mean_cost_per_attempt", "cost_per_attempt"),
        )
        for mean_field, count_field in count_pairs:
            if getattr(record, mean_field) is None:
                continue
            count = (
                getattr(record.observation_counts, count_field)
                if record.observation_counts is not None
                else None
            )
            if count is None:
                failures.append(f"observation count is missing for {mean_field}")
            elif count != record.attempts:
                failures.append(f"observation count does not match attempts for {mean_field}")
    if isinstance(record, TaskEconomicsMeasurement):
        if record.cost_basis != CostBasis.SUCCESSFUL_TASK:
            failures.append("economics record is not successful-task cost")
        if record.aggregation_statistic != AggregationStatistic.ARITHMETIC_MEAN:
            failures.append("economics record is not an arithmetic mean")
        if (
            record.attempts is None
            or record.successful_attempts is None
            or record.cost_observation_count is None
        ):
            failures.append("economics attempt, success, or cost count is missing")
        elif record.cost_observation_count != record.attempts:
            failures.append("economics cost observations do not cover every attempt")
        if record.total_observed_cost_usd is None:
            failures.append("total observed cost is missing")
        if record.billing_evidence != BillingEvidenceKind.PROVIDER_BILLING_RECORD:
            failures.append("provider billing-record evidence is missing")
    if record.source.organization.strip().lower() in {"", "unknown", "unspecified"}:
        failures.append("source organization is unknown")
    if not record.evaluator:
        failures.append("evaluator is missing")
    if not record.benchmark_version:
        failures.append("benchmark or workload version is missing")
    if not record.harness_version:
        failures.append("harness version is missing")
    verification = record.configuration_verification
    if verification is None:
        failures.append("structured configuration verification is missing")
    else:
        if not verification.model_label_exact or not verification.release_label_exact:
            failures.append("model or release label is not exact")
        if not verification.effort_label_exact:
            failures.append("inference effort is not exact")
        if not verification.fallback_absent:
            failures.append("fallback or composite deployment is not ruled out")
        endpoint_sensitive = isinstance(record, TaskEconomicsMeasurement) or (
            isinstance(record, EfficiencyMeasurement)
            and any(
                value is not None
                for value in (
                    record.mean_cached_tokens,
                    record.mean_wall_seconds,
                    record.mean_cost_per_attempt,
                )
            )
        )
        if endpoint_sensitive and not verification.deployment_identity_verified:
            failures.append("deployment identity is not verified for endpoint-sensitive evidence")
        if isinstance(record, TaskEconomicsMeasurement):
            if not verification.endpoint_verified:
                failures.append("economics endpoint is not verified")
            if not verification.service_tier_verified:
                failures.append("economics service tier is not verified")
    if record.capture_type is None or not record.source_artifact_id:
        failures.append("retained source artifact reference is missing")
    if record.cohort_key == "unspecified":
        failures.append("compatibility cohort key is unspecified")
    if IDENTITY_ASSURANCE_ORDER[model.identity_assurance] < IDENTITY_ASSURANCE_ORDER[
        IdentityAssurance.LABEL_EXACT
    ]:
        failures.append("model identity assurance is below label_exact")
    if model.named_release is None:
        failures.append("named release is missing")
    if record.provider_snapshot_id and record.provider_snapshot_id != model.provider_snapshot_id:
        failures.append("provider snapshot does not match the scored configuration")
    if evidence_date(record) is None:
        failures.append("evaluation or source as-of date is missing")
    if model.endpoint_id and record.endpoint_id != model.endpoint_id:
        failures.append("deployment endpoint does not match the scored configuration")
    if model.serving_provider and record.serving_provider != model.serving_provider:
        failures.append("serving provider does not match the scored configuration")
    if model.service_tier and record.service_tier != model.service_tier:
        failures.append("service tier does not match the scored configuration")
    return tuple(failures)


def is_scoring_ready(record: ScoredRecord, model: ModelConfiguration) -> bool:
    return not readiness_failures(record, model)


def scored_records(dataset: Dataset, *, allow_unready: bool = False) -> tuple[Provenance, ...]:
    models = {model.id: model for model in dataset.models}
    records: Iterable[ScoredRecord] = (
        *dataset.benchmarks,
        *dataset.efficiency,
        *dataset.task_economics,
    )
    output: list[Provenance] = []
    for record in records:
        model = models.get(record.model_id)
        if model is None or record.record_status in {
            RecordStatus.DIAGNOSTIC_ONLY,
            RecordStatus.INVALID,
        }:
            continue
        if record.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY:
            continue
        if allow_unready or is_scoring_ready(record, model):
            output.append(record)
    return tuple(output)


def scoring_dataset(dataset: Dataset, *, allow_unready: bool = False) -> tuple[Dataset, bool]:
    models = {model.id: model for model in dataset.models}
    unready_used = False

    def include(record: ScoredRecord) -> bool:
        nonlocal unready_used
        model = models.get(record.model_id)
        if model is None or record.record_status in {
            RecordStatus.DIAGNOSTIC_ONLY,
            RecordStatus.INVALID,
        }:
            return False
        if record.scoring_disposition == ScoringDisposition.DIAGNOSTIC_ONLY:
            return False
        ready = is_scoring_ready(record, model)
        if allow_unready and not ready:
            unready_used = True
        return ready or allow_unready

    return (
        dataset.model_copy(
            update={
                "benchmarks": tuple(item for item in dataset.benchmarks if include(item)),
                "efficiency": tuple(item for item in dataset.efficiency if include(item)),
                "task_economics": tuple(item for item in dataset.task_economics if include(item)),
                "pricing": (),
                # External indexes are diagnostic references in v0.2.1.
                "external_indexes": (),
                "release_claims": (),
                # The scored fingerprint retains the accepted-record audit manifest only.
                "complete_audit_fingerprint": None,
            }
        ),
        unready_used,
    )
