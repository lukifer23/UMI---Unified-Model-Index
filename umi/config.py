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
    OverlapPolicy,
    OverlapRelation,
    ScoringDisposition,
    SignalRole,
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
        supported_efficiency = {
            "effective_input_tokens",
            "effective_output_tokens",
            "effective_reasoning_tokens",
            "effective_cached_tokens",
            "effective_turns",
            "effective_agent_steps",
            "effective_wall_time",
            "effective_tool_calls",
        }
        if not self.efficiency or not set(self.efficiency).issubset(supported_efficiency):
            raise ValueError("efficiency weights contain an unsupported metric")
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


class WorkloadFamilyDefinition(ConfigModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    category: WorkloadCategory
    weight: float = Field(gt=0, le=1)


class WorkloadDefinition(ConfigModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    family: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    weight: float = Field(gt=0, le=1)


class ProjectConfig(ConfigModel):
    weights: WeightConfig
    normalization: NormalizationConfig
    eligibility: EligibilityConfig
    benchmarks: tuple[BenchmarkDefinition, ...]
    families: tuple[BenchmarkFamilyDefinition, ...]
    workload_families: tuple[WorkloadFamilyDefinition, ...]
    workloads: tuple[WorkloadDefinition, ...]
    value: ValueConfig
    overlap: OverlapPolicy = OverlapPolicy()
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

    @model_validator(mode="after")
    def validate_workload_hierarchy(self) -> ProjectConfig:
        family_ids = [item.id for item in self.workload_families]
        workload_ids = [item.id for item in self.workloads]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("workload family IDs must be unique")
        if len(workload_ids) != len(set(workload_ids)):
            raise ValueError("workload IDs must be unique")
        families = {item.id: item for item in self.workload_families}
        for workload in self.workloads:
            if workload.family not in families:
                raise ValueError(f"workload {workload.id} references unknown family")
        for category in self.weights.workload_weights:
            category_families = [
                item for item in self.workload_families if item.category == category
            ]
            if category_families and abs(
                sum(item.weight for item in category_families) - 1.0
            ) > 1e-9:
                raise ValueError(f"workload family weights for {category.value} must sum to 1")
        for family in self.workload_families:
            family_workloads = [item for item in self.workloads if item.family == family.id]
            if not family_workloads:
                raise ValueError(f"workload family {family.id} has no configured workloads")
            if abs(sum(item.weight for item in family_workloads) - 1.0) > 1e-9:
                raise ValueError(f"workload weights for {family.id} must sum to 1")
        return self

    @model_validator(mode="after")
    def validate_overlap_policy(self) -> ProjectConfig:
        signals = {item.id: item for item in self.overlap.signals}
        if len(signals) != len(self.overlap.signals):
            raise ValueError("overlap signal IDs must be unique")
        graph: dict[str, set[str]] = {signal_id: set() for signal_id in signals}
        for edge in self.overlap.edges:
            if edge.source not in signals or edge.target not in signals:
                raise ValueError("overlap edges must reference configured signals")
            if edge.source == edge.target:
                raise ValueError("overlap edges cannot be self-referential")
            graph[edge.source].add(edge.target)
            source = signals[edge.source]
            target = signals[edge.target]
            if (
                source.disposition == ScoringDisposition.SCORED
                and target.disposition == ScoringDisposition.SCORED
                and source.role == target.role
                and edge.relation
                in {
                    OverlapRelation.CONTAINS,
                    OverlapRelation.DERIVED_FROM,
                    OverlapRelation.DUPLICATE_MEASUREMENT,
                    OverlapRelation.SHARED_TASKS,
                    OverlapRelation.SHARED_CONSTRUCT,
                }
                and (source.budget_group is None or source.budget_group != target.budget_group)
            ):
                raise ValueError(
                    f"overlapping scored signals {source.id} and {target.id} must share a budget"
                )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("overlap graph must be acyclic")
            if node in visited:
                return
            visiting.add(node)
            for child in graph[node]:
                visit(child)
            visiting.remove(node)
            visited.add(node)

        for signal_id in sorted(graph):
            visit(signal_id)

        governed = [item for item in self.benchmarks if item.signal_id is not None]
        if governed:
            if len(governed) != len(self.benchmarks):
                raise ValueError("all benchmark definitions must bind a signal policy")
            allocations: dict[str, tuple[Domain, str, str]] = {}
            for benchmark in governed:
                signal = signals.get(benchmark.signal_id or "")
                if signal is None:
                    raise ValueError(f"benchmark {benchmark.id} references unknown signal policy")
                if benchmark.budget_group != signal.budget_group:
                    raise ValueError(f"benchmark {benchmark.id} budget differs from signal policy")
                family = next(item for item in self.families if item.id == benchmark.family)
                if family.weight > 0 and signal.disposition != ScoringDisposition.SCORED:
                    raise ValueError(
                        f"positive-weight benchmark {benchmark.id} is not score-enabled"
                    )
                if (
                    signal.disposition == ScoringDisposition.SCORED
                    and signal.role != SignalRole.TASK
                ):
                    raise ValueError(f"scored benchmark {benchmark.id} must bind a task signal")
                if benchmark.budget_group is not None:
                    allocation = (
                        benchmark.domain,
                        benchmark.family,
                        benchmark.representation_group or benchmark.family,
                    )
                    prior = allocations.setdefault(benchmark.budget_group, allocation)
                    if prior != allocation:
                        raise ValueError(
                            f"budget group {benchmark.budget_group} maps to multiple allocations"
                        )
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
    raw_workloads = _read_yaml(root / "workloads.yaml")
    overlap_path = root / "overlap.yaml"
    raw_overlap = (
        _read_yaml(overlap_path) if overlap_path.is_file() else {"signals": [], "edges": []}
    )
    if not isinstance(raw_benchmarks, dict):
        raise ValueError("benchmarks.yaml must be a mapping")
    if not isinstance(raw_workloads, dict):
        raise ValueError("workloads.yaml must be a mapping")
    canonical = json.dumps(
        {
            "weights": raw_weights,
            "normalization": raw_normalization,
            "eligibility": raw_eligibility,
            "benchmarks": raw_benchmarks,
            "value": raw_value,
            "workloads": raw_workloads,
            "overlap": raw_overlap,
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
        workload_families=tuple(
            WorkloadFamilyDefinition.model_validate(item)
            for item in raw_workloads["families"]
        ),
        workloads=tuple(
            WorkloadDefinition.model_validate(item) for item in raw_workloads["workloads"]
        ),
        value=ValueConfig.model_validate(raw_value),
        overlap=OverlapPolicy.model_validate(raw_overlap),
        fingerprint=hashlib.sha256(canonical.encode()).hexdigest(),
    )
