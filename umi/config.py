from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from umi.schemas import BenchmarkDefinition, Domain, NormalizationStrategy


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
    overall: OverallWeights
    sensitivity_sets: tuple[SensitivityWeights, ...]

    @model_validator(mode="after")
    def validate_weights(self) -> WeightConfig:
        for name, weights in (
            ("capability_domains", self.capability_domains),
            ("efficiency", self.efficiency),
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

    @model_validator(mode="after")
    def validate_ranges(self) -> EligibilityConfig:
        if self.release_start > self.release_end:
            raise ValueError("release_start must not follow release_end")
        if self.high_confidence_coverage < self.medium_confidence_coverage:
            raise ValueError("high confidence coverage must be at least medium")
        return self


class ProjectConfig(ConfigModel):
    weights: WeightConfig
    normalization: NormalizationConfig
    eligibility: EligibilityConfig
    benchmarks: tuple[BenchmarkDefinition, ...]
    fingerprint: str


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_project_config(config_dir: str | Path) -> ProjectConfig:
    root = Path(config_dir)
    raw_weights = _read_yaml(root / "weights.yaml")
    raw_normalization = _read_yaml(root / "normalization.yaml")
    raw_eligibility = _read_yaml(root / "eligibility.yaml")
    raw_benchmarks = _read_yaml(root / "benchmarks.yaml")
    if not isinstance(raw_benchmarks, dict):
        raise ValueError("benchmarks.yaml must be a mapping")
    canonical = json.dumps(
        {
            "weights": raw_weights,
            "normalization": raw_normalization,
            "eligibility": raw_eligibility,
            "benchmarks": raw_benchmarks,
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
        fingerprint=hashlib.sha256(canonical.encode()).hexdigest(),
    )
