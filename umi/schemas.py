from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")]
NonNegative = Annotated[float, Field(ge=0)]
Rate = Annotated[float, Field(ge=0, le=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


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


class ModelConfiguration(StrictModel):
    id: Identifier
    family: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    release_date: date
    configuration: str = Field(min_length=1)
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
    weight: float = Field(gt=0)
    normalization: NormalizationStrategy
    parent_aggregates: tuple[Identifier, ...] = ()
    constituents: tuple[Identifier, ...] = ()
    domain_cap: float = Field(default=1.0, gt=0, le=1)


class BenchmarkMeasurement(Provenance):
    benchmark_id: Identifier
    model_id: Identifier
    value: float
    workload: Identifier | None = None
    evaluation_settings: dict[str, Any] = Field(default_factory=dict)


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


class ComponentScore(StrictModel):
    score: float | None
    coverage: float = Field(ge=0, le=1)
    provisional: bool = False
    source_record_ids: tuple[Identifier, ...] = ()
    diagnostics: tuple[str, ...] = ()


class ScoringResult(StrictModel):
    model_id: Identifier
    capability: ComponentScore
    efficiency: ComponentScore
    economics: ComponentScore
    overall: float | None
    value: float | None
    overall_coverage: float = Field(ge=0, le=1)
    confidence: Confidence
    eligible: bool
    provisional: bool
    capability_domains: tuple[Domain, ...]
    evidence_quality_share: float = Field(ge=0, le=1)
    source_record_ids: tuple[Identifier, ...]
    diagnostics: tuple[str, ...]
    config_fingerprint: str

