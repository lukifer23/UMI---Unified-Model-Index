from __future__ import annotations

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


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfigurationEffort(StrEnum):
    STANDARD = "standard"
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"
    XHIGH = "xhigh"
    CUSTOM = "custom"


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


class Source(StrictModel):
    organization: str = Field(min_length=1)
    url: HttpUrl
    accessed: date


class Provenance(StrictModel):
    record_id: Identifier
    source: Source
    result_type: ResultType
    benchmark_version: str | None = None
    harness_version: str | None = None
    metric_definition: str = Field(min_length=1)
    tools_enabled: bool | None = None
    notes: str | None = None
    evaluator: str | None = None
    harness_owner: str | None = None
    run_executor: str | None = None
    raw_artifact_available: bool | None = None
    reproducible: bool | None = None
    configuration_verified: bool | None = None
    record_status: RecordStatus = RecordStatus.READY
    source_artifact_id: Identifier | None = None
    serving_provider: str | None = None
    endpoint_id: str | None = None
    service_tier: str | None = None


class ModelConfiguration(StrictModel):
    id: Identifier
    family: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    release_date: date
    configuration: ConfigurationEffort
    snapshot_id: Identifier = "unspecified"
    api_model_id: str | None = None
    model_developer: str | None = None
    serving_provider: str | None = None
    endpoint_id: str | None = None
    service_tier: str | None = None
    region: str | None = None
    hardware: str | None = None
    source_snapshot_ids: tuple[Identifier, ...] = ()
    open_weights: bool
    context_window: int | None = Field(default=None, gt=0)
    notes: str | None = None
    synthetic: bool = False


class BenchmarkDefinition(StrictModel):
    id: Identifier
    name: str = Field(min_length=1)
    domain: Domain
    family: Identifier
    direction: Direction
    unit: Unit
    representation_weight: float = Field(default=1.0, gt=0)
    representation_group: Identifier | None = None
    normalization: NormalizationStrategy
    parent_aggregates: tuple[Identifier, ...] = ()
    constituents: tuple[Identifier, ...] = ()


class BenchmarkFamilyDefinition(StrictModel):
    id: Identifier
    domain: Domain
    weight: float = Field(gt=0, le=1)
    cap: float = Field(gt=0, le=1)


class BenchmarkMeasurement(Provenance):
    benchmark_id: Identifier
    model_id: Identifier
    value: float
    cohort_key: Identifier = "unspecified"
    model_snapshot_id: Identifier = "unspecified"
    evaluation_date: date | None = None
    workload: Identifier | None = None
    evaluation_settings: dict[str, Any] = Field(default_factory=dict)
    number_of_tasks: int | None = Field(default=None, gt=0)
    number_of_trials: int | None = Field(default=None, gt=0)
    sample_count: int | None = Field(default=None, gt=0)
    pass_at_k: int | None = Field(default=None, gt=0)
    standard_error: NonNegative | None = None
    confidence_interval: tuple[float, float] | None = None

    @model_validator(mode="after")
    def validate_interval(self) -> BenchmarkMeasurement:
        if self.confidence_interval and self.confidence_interval[0] > self.confidence_interval[1]:
            raise ValueError("confidence interval lower bound must not exceed upper bound")
        return self


class PricingRecord(Provenance):
    model_id: Identifier
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    effective_date: date
    input_per_million: NonNegative | None = None
    cached_input_per_million: NonNegative | None = None
    output_per_million: NonNegative | None = None
    cache_write_per_million: NonNegative | None = None
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
            self.reasoning_token_pricing,
        )
        if not any(value is not None for value in scalar) and not (
            self.long_context_surcharge or self.tool_costs
        ):
            raise ValueError("pricing record must contain at least one price")
        return self


class EfficiencyMeasurement(Provenance):
    model_id: Identifier
    workload: Identifier
    workload_category: WorkloadCategory
    cohort_key: Identifier = "unspecified"
    model_snapshot_id: Identifier = "unspecified"
    evaluation_date: date | None = None
    attempts: int = Field(gt=0)
    success_rate: Rate
    mean_input_tokens: NonNegative | None = None
    mean_output_tokens: NonNegative | None = None
    mean_reasoning_tokens: NonNegative | None = None
    mean_cached_tokens: NonNegative | None = None
    mean_total_tokens: NonNegative | None = None
    mean_turns: NonNegative | None = None
    mean_wall_seconds: NonNegative | None = None
    mean_tool_calls: NonNegative | None = None
    mean_cost_per_attempt: NonNegative | None = None

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
            self.mean_wall_seconds,
            self.mean_tool_calls,
            self.mean_cost_per_attempt,
        )
        if not any(value is not None for value in observed):
            raise ValueError("efficiency record must contain at least one observation")
        return self


class TaskEconomicsMeasurement(Provenance):
    model_id: Identifier
    workload: Identifier
    workload_category: WorkloadCategory
    cohort_key: Identifier
    model_snapshot_id: Identifier
    evaluation_date: date
    cost_basis: CostBasis
    mean_cost_usd: NonNegative
    number_of_tasks: int | None = Field(default=None, gt=0)


class ExternalIndexMeasurement(Provenance):
    index_id: Identifier
    model_id: Identifier
    value: float
    unit: Unit
    direction: Direction
    cohort_key: Identifier
    model_snapshot_id: Identifier
    evaluation_date: date


class SourceSnapshot(StrictModel):
    id: Identifier
    title: str = Field(min_length=1)
    source: Source
    published: date | None = None
    as_of: date
    artifact_path: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    notes: str = Field(min_length=1)


class ComponentScore(StrictModel):
    score: float | None
    coverage: float = Field(ge=0, le=1)
    provisional: bool = False
    source_record_ids: tuple[Identifier, ...] = ()
    diagnostics: tuple[str, ...] = ()
    coverage_details: dict[str, float | int | str] = Field(default_factory=dict)


class CoverageSummary(StrictModel):
    overall_weighted: float = Field(ge=0, le=1)
    capability_domains_represented: int = Field(ge=0)
    capability_domains_total: int = Field(gt=0)
    capability_domain_weighted: float = Field(ge=0, le=1)
    capability_family_weighted: float = Field(ge=0, le=1)
    capability_representation_weighted: float = Field(ge=0, le=1)
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
