from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from umi.schemas import (
    BenchmarkDefinition,
    BenchmarkFamilyDefinition,
    Domain,
    NormalizationStrategy,
    ValueFormula,
    WorkloadCategory,
)


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OverallWeights(ConfigModel):
    capability: float = Field(ge=0)
    efficiency: float = Field(ge=0)
    economics: float = Field(ge=0)

    @model_validator(mode="after")
    def sums_to_one(self) -> OverallWeights:
        if abs(self.capability + self.efficiency + self.economics - 1.0) > 1e-9:
            raise ValueError("overall weights must sum to 1")
        return self


class SensitivityWeights(OverallWeights):
    name: str = Field(min_length=1)


class WeightConfig(ConfigModel):
    capability_domains: dict[Domain, float]
    efficiency: dict[str, float]
    workload_weights: dict[WorkloadCategory, float]
    overall: OverallWeights
    sensitivity_sets: tuple[SensitivityWeights, ...]

    @model_validator(mode="after")
    def validate_weights(self) -> WeightConfig:
        for name, weights in (
            ("capability_domains", self.capability_domains),
            ("efficiency", self.efficiency),
            ("workload_weights", self.workload_weights),
        ):
            if (
                any(value < 0 for value in weights.values())
                or abs(sum(weights.values()) - 1) > 1e-9
            ):
                raise ValueError(f"{name} weights must be nonnegative and sum to 1")
        return self


class NormalizationConfig(ConfigModel):
    minimum_robust_cohort: int = Field(ge=2)
    minimum_rank_cohort: int = Field(ge=2)
    correlation_min_overlap: int = Field(ge=2)
    default_strategy: NormalizationStrategy
    log_metrics: tuple[str, ...]


class EligibilityConfig(ConfigModel):
    release_start: date
    release_end: date
    minimum_overall_coverage: float = Field(ge=0, le=1)
    minimum_capability_domains: int = Field(ge=1)
    high_confidence_coverage: float = Field(ge=0, le=1)
    high_confidence_quality_share: float = Field(ge=0, le=1)
    medium_confidence_coverage: float = Field(ge=0, le=1)
    medium_confidence_quality_share: float = Field(ge=0, le=1)
    minimum_efficiency_workload_coverage: float = Field(default=0.50, ge=0, le=1)
    minimum_component_coverage: dict[str, float]

    @model_validator(mode="after")
    def validate_ranges(self) -> EligibilityConfig:
        if self.release_start > self.release_end:
            raise ValueError("release_start must not follow release_end")
        if self.high_confidence_coverage < self.medium_confidence_coverage:
            raise ValueError("high confidence coverage must be at least medium")
        required = {"capability", "efficiency", "economics"}
        if set(self.minimum_component_coverage) != required:
            raise ValueError(
                "minimum_component_coverage must define capability, efficiency, economics"
            )
        if any(not 0 <= value <= 1 for value in self.minimum_component_coverage.values()):
            raise ValueError("minimum component coverage values must be between 0 and 1")
        return self


class ValueScenario(ConfigModel):
    name: str = Field(min_length=1)
    formula: ValueFormula
    alpha: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_formula_parameters(self) -> ValueScenario:
        if self.formula == ValueFormula.WEIGHTED_GEOMETRIC and self.alpha is None:
            raise ValueError("weighted geometric Value scenarios require alpha")
        if self.formula != ValueFormula.WEIGHTED_GEOMETRIC and self.alpha is not None:
            raise ValueError("alpha is only valid for weighted geometric Value scenarios")
        return self

    def mathematical_signature(self) -> tuple[str, float | None]:
        if self.formula == ValueFormula.GEOMETRIC:
            return (ValueFormula.WEIGHTED_GEOMETRIC.value, 0.5)
        return (self.formula.value, self.alpha)


class ValueConfig(ConfigModel):
    baseline: str = Field(min_length=1)
    scenarios: tuple[ValueScenario, ...]

    @model_validator(mode="after")
    def validate_scenarios(self) -> ValueConfig:
        names = [scenario.name for scenario in self.scenarios]
        if len(names) != len(set(names)):
            raise ValueError("Value scenario names must be unique")
        if self.baseline not in names:
            raise ValueError("Value baseline must name a configured scenario")
        signatures = [scenario.mathematical_signature() for scenario in self.scenarios]
        if len(signatures) != len(set(signatures)):
            raise ValueError("Value scenarios must be mathematically distinct")
        if len(signatures) < 2:
            raise ValueError("at least two distinct Value scenarios are required")
        return self

    @property
    def baseline_scenario(self) -> ValueScenario:
        return next(item for item in self.scenarios if item.name == self.baseline)


class ProjectConfig(ConfigModel):
    weights: WeightConfig
    normalization: NormalizationConfig
    eligibility: EligibilityConfig
    benchmarks: tuple[BenchmarkDefinition, ...]
    families: tuple[BenchmarkFamilyDefinition, ...]
    value: ValueConfig
    fingerprint: str

    @model_validator(mode="after")
    def validate_family_budgets(self) -> ProjectConfig:
        family_ids = {item.id for item in self.families}
        if len(family_ids) != len(self.families):
            raise ValueError("benchmark family IDs must be unique")
        for benchmark in self.benchmarks:
            family = next((item for item in self.families if item.id == benchmark.family), None)
            if family is None:
                raise ValueError(f"benchmark {benchmark.id} references unknown family")
            if family.domain != benchmark.domain:
                raise ValueError(f"benchmark {benchmark.id} domain differs from its family")
        for domain in self.weights.capability_domains:
            domain_families = [item for item in self.families if item.domain == domain]
            weights = [item.weight for item in domain_families]
            if weights and abs(sum(weights) - 1.0) > 1e-9:
                raise ValueError(f"family weights for {domain.value} must sum to 1")
            if any(item.weight > item.cap for item in domain_families):
                raise ValueError(f"family weight exceeds cap in {domain.value}")
            if domain_families and sum(item.cap for item in domain_families) < 1.0 - 1e-9:
                raise ValueError(f"family caps for {domain.value} must sum to at least 1")
        return self


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_project_config(config_dir: str | Path) -> ProjectConfig:
    root = Path(config_dir)
    raw_weights = _read_yaml(root / "weights.yaml")
    raw_normalization = _read_yaml(root / "normalization.yaml")
    raw_eligibility = _read_yaml(root / "eligibility.yaml")
    raw_benchmarks = _read_yaml(root / "benchmarks.yaml")
    raw_value = _read_yaml(root / "value.yaml")
    if not isinstance(raw_benchmarks, dict):
        raise ValueError("benchmarks.yaml must be a mapping")
    canonical = json.dumps(
        {
            "weights": raw_weights,
            "normalization": raw_normalization,
            "eligibility": raw_eligibility,
            "benchmarks": raw_benchmarks,
            "value": raw_value,
        },
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return ProjectConfig(
        weights=WeightConfig.model_validate(raw_weights),
        normalization=NormalizationConfig.model_validate(raw_normalization),
        eligibility=EligibilityConfig.model_validate(raw_eligibility),
        benchmarks=tuple(
            BenchmarkDefinition.model_validate(item) for item in raw_benchmarks["benchmarks"]
        ),
        families=tuple(
            BenchmarkFamilyDefinition.model_validate(item) for item in raw_benchmarks["families"]
        ),
        value=ValueConfig.model_validate(raw_value),
        fingerprint=hashlib.sha256(canonical.encode()).hexdigest(),
    )
