from __future__ import annotations

import math
from datetime import date
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")]
NonNegative = Annotated[float, Field(ge=0)]
Rate = Annotated[float, Field(ge=0, le=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class ResultType(StrEnum):
    INDEPENDENT = "independent"
    COMMUNITY = "community_reproduction"
    VENDOR = "vendor_reported"
    DERIVED = "derived"


class Direction(StrEnum):
    HIGHER = "higher"
    LOWER = "lower"


class Domain(StrEnum):
    GENERAL = "general_reasoning"
    SOFTWARE = "software_engineering"
    AGENTIC = "agentic_work"
    MATH = "math_science"
    CONTEXT = "context_reliability"


class Unit(StrEnum):
    PERCENT = "percent"
    SCORE = "score"
    TOKENS = "tokens"
    SECONDS = "seconds"
    TURNS = "turns"
    CALLS = "calls"
    USD = "usd"


class NormalizationStrategy(StrEnum):
    ROBUST_Z = "robust_z"
    PERCENTILE = "percentile"


class ScaleKind(StrEnum):
    RAW_METRIC = "raw_metric"
    STABLE_PANEL_PERCENTILE = "stable_panel_percentile"
    WEIGHTED_STABLE_PANEL_COMPOSITE = "weighted_stable_panel_composite"
    ANCHORED_SCORE = "anchored_score"
    LATENT_ESTIMATE = "latent_estimate"


class ComparisonStatus(StrEnum):
    OK = "ok"
    INSUFFICIENT_COMMON_SUPPORT = "insufficient_common_support"


class CertificateStatus(StrEnum):
    VALID_COMPARISON = "valid_comparison"
    PROVISIONAL_COMPARISON = "provisional_comparison"
    INSUFFICIENT_COMMON_SUPPORT = "insufficient_common_support"
    INVALID_BUNDLE = "invalid_bundle"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UncertaintyKind(StrEnum):
    CONFIDENCE_INTERVAL = "confidence_interval"
    PUBLISHED_MARGIN = "published_margin"
    STANDARD_ERROR = "standard_error"


class ConfigurationEffort(StrEnum):
    STANDARD = "standard"
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"
    XHIGH = "xhigh"
    CUSTOM = "custom"


class IdentityKind(StrEnum):
    IMMUTABLE_PROVIDER_SNAPSHOT = "immutable_provider_snapshot"
    IMMUTABLE_OPEN_WEIGHT_REVISION = "immutable_open_weight_revision"
    PROVIDER_VERSIONED_ENDPOINT = "provider_versioned_endpoint"
    DATED_ENDPOINT_ALIAS = "dated_endpoint_alias"
    NAMED_RELEASE = "named_release"
    MARKETING_CONFIGURATION = "marketing_configuration"
    UNKNOWN = "unknown"


class IdentityAssurance(StrEnum):
    VERIFIED = "verified"
    STRONGLY_SUPPORTED = "strongly_supported"
    LABEL_EXACT = "label_exact"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class WorkloadCategory(StrEnum):
    CODING = "coding_agents"
    RESEARCH = "research_analysis"
    TOOL_USE = "tool_use_agents"
    BROWSER = "browser_computer_use"
    GENERAL = "general_interaction"
    LONG_HORIZON = "long_horizon"


class ValueFormula(StrEnum):
    GEOMETRIC = "geometric_mean_v1"
    WEIGHTED_GEOMETRIC = "weighted_geometric_v1"
    HARMONIC = "harmonic_mean_v1"


class CostBasis(StrEnum):
    ATTEMPTED_TASK = "attempted_task"
    SUCCESSFUL_TASK = "successful_task"


class RecordStatus(StrEnum):
    READY = "ready"
    DIAGNOSTIC_ONLY = "diagnostic_only"
    SYNTHETIC = "synthetic"
    INVALID = "invalid"


class AggregationStatistic(StrEnum):
    ARITHMETIC_MEAN = "arithmetic_mean"
    MEDIAN = "median"
    TOTAL = "total"
    UNSPECIFIED = "unspecified"


class SignalRole(StrEnum):
    COMPOSITE = "composite"
    PREFERENCE = "preference"
    TASK = "task"
    EFFICIENCY = "efficiency"
    ECONOMICS = "economics"
    REFERENCE = "reference"


class ScoringDisposition(StrEnum):
    SCORED = "scored"
    DIAGNOSTIC_ONLY = "diagnostic_only"


class CrosswalkStatus(StrEnum):
    EXACT = "exact"
    REJECTED = "rejected"


class OverlapRelation(StrEnum):
    CONTAINS = "contains"
    DERIVED_FROM = "derived_from"
    DUPLICATE_MEASUREMENT = "duplicate_measurement"
    SHARED_TASKS = "shared_tasks"
    SHARED_CONSTRUCT = "shared_construct"
    UNKNOWN_OVERLAP = "unknown_overlap"


class RedistributionScope(StrEnum):
    FULL_ARTIFACT = "full_artifact"
    FACTS_ONLY = "facts_only"
    REFERENCE_ONLY = "reference_only"


class ArtifactCaptureType(StrEnum):
    RAW_UPSTREAM_PAYLOAD = "raw_upstream_payload"
    ARCHIVED_SOURCE_SNAPSHOT = "archived_source_snapshot"
    REVIEWED_FACT_EXTRACT = "reviewed_fact_extract"
    CITATION_ONLY = "citation_only"
    DERIVED_ARTIFACT = "derived_artifact"


class Source(StrictModel):
    organization: str = Field(min_length=1)
    url: HttpUrl
    accessed: date


class ConfigurationVerification(StrictModel):
    model_label_exact: bool = False
    release_label_exact: bool = False
    effort_label_exact: bool = False
    fallback_absent: bool = False
    provider_snapshot_verified: bool = False
    endpoint_verified: bool = False
    service_tier_verified: bool = False
    deployment_identity_verified: bool = False


class Provenance(StrictModel):
    record_id: Identifier
    source: Source
    model_release_date: date | None = None
    measurement_as_of_date: date | None = None
    leaderboard_publish_date: date | None = None
    source_published_date: date | None = None
    result_type: ResultType
    benchmark_version: str | None = None
    harness_version: str | None = None
    metric_definition: str = Field(min_length=1)
    tools_enabled: bool | None = None
    notes: str | None = None
    evaluator: str | None = None
    harness_owner: str | None = None
    run_executor: str | None = None
    capture_type: ArtifactCaptureType | None = None
    reproducible: bool | None = None
    configuration_verification: ConfigurationVerification | None = None
    record_status: RecordStatus = RecordStatus.READY
    source_artifact_id: Identifier | None = None
    source_registry_snapshot_id: Identifier | None = None
    crosswalk_entry_id: Identifier | None = None
    signal_id: Identifier | None = None
    source_model_id: str | None = None
    provider_snapshot_id: str | None = None
    serving_provider: str | None = None
    endpoint_id: str | None = None
    service_tier: str | None = None
    signal_role: SignalRole = SignalRole.TASK
    scoring_disposition: ScoringDisposition = ScoringDisposition.SCORED


class AcceptanceManifest(StrictModel):
    accepted_record_ids: tuple[Identifier, ...]
    excluded_diagnostic_record_ids: tuple[Identifier, ...]
    excluded_unready_record_ids: tuple[Identifier, ...]
    accepted_artifact_ids: tuple[Identifier, ...]
    accepted_crosswalk_entry_ids: tuple[Identifier, ...]
    accepted_signal_ids: tuple[Identifier, ...]
    scoring_relevant_adapter_versions: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class ModelConfiguration(StrictModel):
    id: Identifier
    family: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    release_date: date
    configuration: ConfigurationEffort
    identity_kind: IdentityKind = IdentityKind.UNKNOWN
    identity_assurance: IdentityAssurance = IdentityAssurance.UNKNOWN
    named_release: str | None = None
    provider_snapshot_id: str | None = None
    open_weight_revision: str | None = None
    api_model_id: str | None = None
    model_developer: str | None = None
    serving_provider: str | None = None
    endpoint_id: str | None = None
    service_tier: str | None = None
    region: str | None = None
    hardware: str | None = None
    evidence_artifact_ids: tuple[Identifier, ...] = ()
    open_weights: bool
    context_window: int | None = Field(default=None, gt=0)
    notes: str | None = None
    synthetic: bool = False


class BenchmarkDefinition(StrictModel):
    id: Identifier
    name: str = Field(min_length=1)
    domain: Domain
    family: Identifier
    signal_id: Identifier | None = None
    budget_group: Identifier | None = None
    direction: Direction
    unit: Unit
    representation_weight: float = Field(default=1.0, gt=0)
    representation_group: Identifier | None = None
    selection_priority: int = Field(default=0, ge=0)
    normalization: NormalizationStrategy
    parent_aggregates: tuple[Identifier, ...] = ()
    constituents: tuple[Identifier, ...] = ()


class BenchmarkFamilyDefinition(StrictModel):
    id: Identifier
    domain: Domain
    weight: float = Field(ge=0, le=1)
    cap: float = Field(gt=0, le=1)


class MeasurementUncertainty(StrictModel):
    """Literal uncertainty metadata supplied by one source record."""

    kind: UncertaintyKind
    lower: float | None = None
    upper: float | None = None
    margin: NonNegative | None = None
    standard_error: NonNegative | None = None
    confidence_level: Rate | None = None
    source_fields: tuple[str, ...] = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_declared_form(self) -> MeasurementUncertainty:
        if self.kind == UncertaintyKind.CONFIDENCE_INTERVAL:
            if self.lower is None or self.upper is None or self.lower > self.upper:
                raise ValueError("confidence interval requires ordered lower and upper bounds")
        if self.kind == UncertaintyKind.PUBLISHED_MARGIN and self.margin is None:
            raise ValueError("published margin requires a margin")
        if self.kind == UncertaintyKind.STANDARD_ERROR and self.standard_error is None:
            raise ValueError("standard error requires standard_error")
        return self


class BenchmarkMeasurement(Provenance):
    benchmark_id: Identifier
    model_id: Identifier
    value: float
    cohort_key: Identifier = "unspecified"
    evaluation_date: date | None = None
    workload: Identifier | None = None
    evaluation_settings: dict[str, Any] = Field(default_factory=dict)
    number_of_tasks: int | None = Field(default=None, gt=0)
    number_of_trials: int | None = Field(default=None, gt=0)
    sample_count: int | None = Field(default=None, gt=0)
    pass_at_k: int | None = Field(default=None, gt=0)
    uncertainty: MeasurementUncertainty | None = None


class PricingRecord(Provenance):
    model_id: Identifier
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    effective_date: date
    input_per_million: NonNegative | None = None
    cached_input_per_million: NonNegative | None = None
    output_per_million: NonNegative | None = None
    cache_write_per_million: NonNegative | None = None
    cache_write_1h_per_million: NonNegative | None = None
    reasoning_token_pricing: NonNegative | None = None
    long_context_surcharge: dict[str, NonNegative] = Field(default_factory=dict)
    tool_costs: dict[str, NonNegative] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_a_price(self) -> PricingRecord:
        scalar = (
            self.input_per_million,
            self.cached_input_per_million,
            self.output_per_million,
            self.cache_write_per_million,
            self.cache_write_1h_per_million,
            self.reasoning_token_pricing,
        )
        if not any(value is not None for value in scalar) and not (
            self.long_context_surcharge or self.tool_costs
        ):
            raise ValueError("pricing record must contain at least one price")
        return self


class EfficiencyObservationCounts(StrictModel):
    """Attempt counts contributing to each arithmetic-mean resource field."""

    input_tokens: int | None = Field(default=None, gt=0)
    output_tokens: int | None = Field(default=None, gt=0)
    reasoning_tokens: int | None = Field(default=None, gt=0)
    cached_tokens: int | None = Field(default=None, gt=0)
    total_tokens: int | None = Field(default=None, gt=0)
    turns: int | None = Field(default=None, gt=0)
    agent_steps: int | None = Field(default=None, gt=0)
    wall_seconds: int | None = Field(default=None, gt=0)
    tool_calls: int | None = Field(default=None, gt=0)
    cost_per_attempt: int | None = Field(default=None, gt=0)


class EfficiencyMeasurement(Provenance):
    model_id: Identifier
    workload: Identifier
    workload_category: WorkloadCategory
    cohort_key: Identifier = "unspecified"
    evaluation_date: date | None = None
    attempts: int = Field(gt=0)
    successful_attempts: int | None = Field(default=None, ge=0)
    success_rate: Rate
    mean_input_tokens: NonNegative | None = None
    mean_output_tokens: NonNegative | None = None
    mean_reasoning_tokens: NonNegative | None = None
    mean_cached_tokens: NonNegative | None = None
    mean_total_tokens: NonNegative | None = None
    mean_turns: NonNegative | None = None
    mean_agent_steps: NonNegative | None = None
    mean_wall_seconds: NonNegative | None = None
    mean_tool_calls: NonNegative | None = None
    mean_cost_per_attempt: NonNegative | None = None
    observed_output_tokens_summary: NonNegative | None = None
    observed_agent_steps_summary: NonNegative | None = None
    observed_cost_summary_usd: NonNegative | None = None
    aggregation_statistic: AggregationStatistic = AggregationStatistic.ARITHMETIC_MEAN
    observation_counts: EfficiencyObservationCounts | None = None

    @field_validator("workload_category", mode="before")
    @classmethod
    def migrate_legacy_workload_category(cls, value: object) -> object:
        aliases = {
            "agentic": WorkloadCategory.TOOL_USE,
            "coding": WorkloadCategory.CODING,
            "research": WorkloadCategory.RESEARCH,
            "browser": WorkloadCategory.BROWSER,
            "general": WorkloadCategory.GENERAL,
        }
        return aliases.get(value, value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_observation(self) -> EfficiencyMeasurement:
        observed = (
            self.mean_input_tokens,
            self.mean_output_tokens,
            self.mean_reasoning_tokens,
            self.mean_cached_tokens,
            self.mean_total_tokens,
            self.mean_turns,
            self.mean_agent_steps,
            self.mean_wall_seconds,
            self.mean_tool_calls,
            self.mean_cost_per_attempt,
            self.observed_output_tokens_summary,
            self.observed_agent_steps_summary,
            self.observed_cost_summary_usd,
        )
        if not any(value is not None for value in observed):
            raise ValueError("efficiency record must contain at least one observation")
        if self.successful_attempts is not None:
            if self.successful_attempts > self.attempts:
                raise ValueError("successful_attempts cannot exceed attempts")
            reconciled_rate = self.successful_attempts / self.attempts
            if not math.isclose(self.success_rate, reconciled_rate, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(
                    "success_rate does not reconcile with successful_attempts/attempts"
                )
        if self.observation_counts is not None:
            field_pairs = (
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
            for mean_field, count_field in field_pairs:
                count = getattr(self.observation_counts, count_field)
                value = getattr(self, mean_field)
                if count is not None and value is None:
                    raise ValueError(f"{count_field} count has no corresponding {mean_field}")
                if count is not None and count > self.attempts:
                    raise ValueError(f"{count_field} count cannot exceed attempts")
        return self


class TaskEconomicsMeasurement(Provenance):
    model_id: Identifier
    workload: Identifier
    workload_category: WorkloadCategory
    cohort_key: Identifier
    evaluation_date: date
    cost_basis: CostBasis
    mean_cost_usd: NonNegative
    number_of_tasks: int | None = Field(default=None, gt=0)
    aggregation_statistic: AggregationStatistic = AggregationStatistic.ARITHMETIC_MEAN


class ExternalIndexMeasurement(Provenance):
    index_id: Identifier
    model_id: Identifier
    value: float
    unit: Unit
    direction: Direction
    cohort_key: Identifier
    evaluation_date: date | None = None


class ReleaseClaim(Provenance):
    """Literal lab release claim retained for descriptive calibration only."""

    claim_text: str = Field(min_length=1)
    model_id: Identifier
    benchmark_id: Identifier
    value: float
    unit: Unit
    direction: Direction
    cohort_key: Identifier
    evaluation_date: date

    @model_validator(mode="after")
    def diagnostic_only(self) -> ReleaseClaim:
        if self.record_status != RecordStatus.DIAGNOSTIC_ONLY:
            raise ValueError("release claims must be diagnostic-only")
        if self.scoring_disposition != ScoringDisposition.DIAGNOSTIC_ONLY:
            raise ValueError("release claims cannot be scored")
        return self


class SourceSnapshot(StrictModel):
    id: Identifier
    title: str = Field(min_length=1)
    source: Source
    published: date | None = None
    as_of: date
    artifact_path: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: str = Field(default="application/yaml", min_length=1)
    upstream_revision: str = Field(default="manual", min_length=1)
    adapter_id: Identifier = "reviewed-facts-v1"
    license_id: str = Field(default="documented-legacy", min_length=1)
    license_url: HttpUrl | None = None
    attribution: str = Field(default="See source URL", min_length=1)
    redistribution_scope: RedistributionScope = RedistributionScope.FACTS_ONLY
    notes: str = Field(min_length=1)


class ModelCrosswalkEntry(StrictModel):
    id: Identifier
    source_id: Identifier
    source_artifact_id: Identifier
    upstream_revision: str = Field(min_length=1)
    source_model_id: str = Field(min_length=1)
    source_effort: ConfigurationEffort | None
    canonical_model_id: Identifier | None
    canonical_effort: ConfigurationEffort | None
    match_evidence: str = Field(min_length=1)
    status: CrosswalkStatus
    rejection_reason: str | None = None

    @model_validator(mode="after")
    def exact_match_is_complete(self) -> ModelCrosswalkEntry:
        if self.status == CrosswalkStatus.EXACT:
            if self.source_effort is None or self.canonical_effort is None:
                raise ValueError("exact crosswalk entries require source and canonical effort")
            if self.canonical_model_id is None:
                raise ValueError("exact crosswalk entries require a canonical model")
            if self.source_effort != self.canonical_effort:
                raise ValueError("exact crosswalk effort must match canonical effort")
            if self.rejection_reason is not None:
                raise ValueError("exact crosswalk entries cannot have a rejection reason")
        elif not self.rejection_reason:
            raise ValueError("rejected crosswalk entries require a rejection reason")
        return self


class ModelCrosswalk(StrictModel):
    entries: tuple[ModelCrosswalkEntry, ...]


class SignalPolicy(StrictModel):
    id: Identifier
    role: SignalRole
    disposition: ScoringDisposition
    budget_group: Identifier | None = None


class OverlapEdge(StrictModel):
    source: Identifier
    target: Identifier
    relation: OverlapRelation
    evidence: str = Field(min_length=1)


class OverlapPolicy(StrictModel):
    signals: tuple[SignalPolicy, ...] = ()
    edges: tuple[OverlapEdge, ...] = ()


class ComponentScore(StrictModel):
    score: float | None
    coverage: float = Field(ge=0, le=1)
    provisional: bool = False
    source_record_ids: tuple[Identifier, ...] = ()
    diagnostics: tuple[str, ...] = ()
    coverage_details: dict[str, float | int | str] = Field(default_factory=dict)
    evidence_profile: EvidenceProfile | None = None
    directly_comparable_model_ids: tuple[Identifier, ...] = ()
    comparability_status: str = "insufficient_common_support"
    comparability_reasons: tuple[str, ...] = ()
    evidence_profile_id: str | None = None
    normalization_panel_ids: tuple[str, ...] = ()
    score_scale_id: str | None = None
    score_semantics: str = "unscored"


class NormalizationTrace(StrictModel):
    requested_strategy: NormalizationStrategy
    applied_strategy: str = Field(min_length=1)
    cohort_size: int = Field(ge=0)
    minimum_robust_cohort: int = Field(gt=0)
    minimum_rank_cohort: int = Field(gt=0)
    fallback_reason: str | None = None
    log_transform: bool
    direction_inverted: bool
    provisional: bool


class NormalizationPanel(StrictModel):
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    benchmark_id: Identifier
    cohort_key: Identifier
    canonical_representation_group: Identifier
    model_ids: tuple[Identifier, ...]
    cohort_roles: dict[Identifier, str]
    requested_strategy: NormalizationStrategy
    applied_strategy: str
    cohort_size: int = Field(ge=0)
    transformation: str
    config_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    scored_input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalization_trace: NormalizationTrace


class ScoreScale(StrictModel):
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    scale_kind: ScaleKind
    evidence_profile_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalization_panel_ids: tuple[str, ...]
    formula_version: str
    normalization_version: str
    config_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


class BenchmarkContribution(StrictModel):
    benchmark_id: Identifier
    cohort_key: Identifier
    raw_value: float
    raw_unit: Unit
    direction: Direction
    source_uncertainty: MeasurementUncertainty | None = None
    configured_absolute_weight: float = Field(ge=0, le=1)
    requested_normalization: NormalizationStrategy
    applied_normalization: str
    normalization_panel_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalized_value: float
    weighted_contribution: float
    normalization_trace: NormalizationTrace
    source_record_ids: tuple[Identifier, ...]


class RawBenchmarkResult(StrictModel):
    benchmark_id: Identifier
    cohort_key: Identifier
    raw_value: float
    raw_unit: Unit
    direction: Direction
    source_uncertainty: MeasurementUncertainty | None = None


class SensitivityInterval(StrictModel):
    record_id: Identifier
    model_id: Identifier
    benchmark_id: Identifier
    lower: float
    upper: float
    interval_origin: str
    assumption: str | None = None
    z_value: float | None = None


class RankRobustness(StrictModel):
    central_estimate_rank: float
    possible_rank_min: float
    possible_rank_max: float
    possible_ranks: tuple[float, ...]
    central_composite_score: float
    composite_score_min: float
    composite_score_max: float
    robustly_dominates: tuple[Identifier, ...]
    robustly_dominated_by: tuple[Identifier, ...]
    scenario_count: int = Field(gt=0)
    exhaustive: bool
    uncertainty_mode: str
    assumptions: tuple[str, ...]


class ComparisonModelScore(StrictModel):
    model_id: Identifier
    score: float
    normalized_composite_score: float
    coverage: float = Field(ge=0, le=1)
    provisional: bool
    rank: float
    evidence_profile_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalization_panel_ids: tuple[str, ...]
    score_scale_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    score_semantics: str
    primary_raw_results: tuple[RawBenchmarkResult, ...]
    contributions: tuple[BenchmarkContribution, ...]
    rank_robustness: RankRobustness | None = None


class CapabilityComparisonResult(StrictModel):
    status: ComparisonStatus
    comparison_group_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    comparison_model_ids: tuple[Identifier, ...]
    common_evidence_profile_id: str | None = None
    common_benchmark_series: tuple[dict[str, str], ...] = ()
    scores: tuple[ComparisonModelScore, ...] = ()
    missing_support_by_model: dict[Identifier, tuple[str, ...]] = Field(default_factory=dict)
    incompatible_series: tuple[str, ...] = ()
    recommended_missing_evidence: tuple[str, ...] = ()
    normalization_panels: tuple[NormalizationPanel, ...] = ()
    score_scale: ScoreScale | None = None
    normalization_method: str
    primary_result_semantics: str
    sensitivity_intervals: tuple[SensitivityInterval, ...] = ()
    publication_label: str


class ComparisonCertificate(StrictModel):
    certificate_version: str
    status: CertificateStatus
    publication_label: str
    comparison_group_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    bundle_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    scored_input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_profile_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    normalization_panel_ids: tuple[str, ...] = ()
    score_scale_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    comparison_model_ids: tuple[Identifier, ...]
    common_benchmark_series: tuple[dict[str, str], ...] = ()
    raw_contributions: dict[Identifier, tuple[RawBenchmarkResult, ...]] = Field(
        default_factory=dict
    )
    normalized_contributions: dict[Identifier, tuple[BenchmarkContribution, ...]] = Field(
        default_factory=dict
    )
    component_scores: dict[Identifier, float] = Field(default_factory=dict)
    central_estimate_ranks: dict[Identifier, float] = Field(default_factory=dict)
    rank_robustness: dict[Identifier, RankRobustness] = Field(default_factory=dict)
    coverage: dict[Identifier, float] = Field(default_factory=dict)
    identity_assurance: dict[Identifier, IdentityAssurance]
    source_record_ids: tuple[Identifier, ...] = ()
    source_artifact_ids: tuple[Identifier, ...] = ()
    source_artifact_checksums: dict[Identifier, str] = Field(default_factory=dict)
    applied_normalization: tuple[NormalizationPanel, ...] = ()
    comparability_basis: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    abstention_reasons: tuple[str, ...] = ()
    missing_evidence: dict[Identifier, tuple[str, ...]] = Field(default_factory=dict)
    result_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


class EvidenceBenchmarkSeries(StrictModel):
    benchmark_id: Identifier
    cohort_key: Identifier
    domain: Domain
    family: Identifier
    representation_group: Identifier
    signal_id: Identifier
    budget_group: Identifier


class EvidenceProfile(StrictModel):
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    estimate_scope: str = Field(min_length=1)
    benchmark_series: tuple[EvidenceBenchmarkSeries, ...] = ()
    workload_series: tuple[str, ...] = ()
    workload_category_ids: tuple[WorkloadCategory, ...] = ()
    workload_family_ids: tuple[Identifier, ...] = ()
    domain_ids: tuple[Domain, ...] = ()
    family_ids: tuple[Identifier, ...] = ()
    source_organizations: tuple[str, ...] = ()
    contributing_record_ids: tuple[Identifier, ...] = ()
    methodology_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_record_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


class CoverageSummary(StrictModel):
    overall_weighted: float = Field(ge=0, le=1)
    capability_domains_represented: int = Field(ge=0)
    capability_domains_total: int = Field(gt=0)
    capability_absolute_weighted: float = Field(ge=0, le=1)
    capability_families_represented: int = Field(ge=0)
    capability_families_total: int = Field(ge=0)
    capability_representations_represented: int = Field(ge=0)
    capability_representations_total: int = Field(ge=0)
    efficiency_workloads_represented: int = Field(ge=0)
    efficiency_workloads_total: int = Field(gt=0)
    efficiency_workload_weighted: float = Field(ge=0, le=1)
    efficiency_metric_weighted: float = Field(ge=0, le=1)
    efficiency_category_metric_coverage: dict[str, float] = Field(default_factory=dict)
    economics_workloads_represented: int = Field(ge=0)
    economics_workloads_total: int = Field(gt=0)
    economics_workload_weighted: float = Field(ge=0, le=1)
    independent_or_community_evidence_share: float = Field(ge=0, le=1)
    source_organization_count: int = Field(ge=0)


class ScoringResult(StrictModel):
    model_id: Identifier
    publication_label: str = "provisional result"
    release_date: date
    capability: ComponentScore
    efficiency: ComponentScore
    economics: ComponentScore
    partial_overall_estimate: float | None
    headline_overall: float | None
    value: float | None
    value_scenario: str
    value_formula: ValueFormula
    value_parameters: dict[str, float] = Field(default_factory=dict)
    overall_coverage: float = Field(ge=0, le=1)
    confidence: Confidence
    eligible: bool
    scoring_ready: bool
    provisional: bool
    capability_domains: tuple[Domain, ...]
    independent_or_community_evidence_share: float = Field(ge=0, le=1)
    source_record_ids: tuple[Identifier, ...]
    diagnostics: tuple[str, ...]
    confidence_reasons: tuple[str, ...]
    coverage: CoverageSummary
    cohort_id: str
    cohort_model_ids: tuple[Identifier, ...]
    dataset_fingerprint: str
    scored_data_fingerprint: str
    data_as_of: date
    release_window_start: date
    release_window_end: date
    engine_version: str
    normalization_version: str
    config_fingerprint: str
    formula_version: str
