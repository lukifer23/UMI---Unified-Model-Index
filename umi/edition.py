"""Edition identifiers and v0.4 Public policy loading."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).resolve().parents[1]
LEGACY_EDITION_ID = "umi-public-v0.3-legacy"
PUBLIC_EDITION_ID = "umi-public-v0.4"
GOVERNED_EDITION_ID = "umi-public-v0.5"
PUBLIC_EDITION_IDS = {
    PUBLIC_EDITION_ID: "umi-methodology-v0.4.0",
    GOVERNED_EDITION_ID: "umi-methodology-v0.5.0",
}


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EntityKind(StrEnum):
    SINGLE_MODEL_SERVICE = "single_model_service"
    FALLBACK_COMPOSITE_SERVICE = "fallback_composite_service"
    ROUTER_COMPOSITE_SERVICE = "router_composite_service"
    OPEN_WEIGHT_DEPLOYMENT = "open_weight_deployment"


class PublicDomain(StrEnum):
    GENERAL_REASONING_AND_KNOWLEDGE = "general_reasoning_and_knowledge"
    SOFTWARE_ENGINEERING = "software_engineering"
    AGENTIC_AND_TOOL_MEDIATED_WORK = "agentic_and_tool_mediated_work"
    MATHEMATICS_AND_SCIENCE = "mathematics_and_science"
    CONTEXT_RELIABILITY_AND_FACTUAL_DISCIPLINE = "context_reliability_and_factual_discipline"
    LANGUAGE_DATA_AND_INSTRUCTION_FOLLOWING = "language_data_and_instruction_following"


class OperationalEfficiencySubcomponent(StrEnum):
    TASK_RESOURCE_INTENSITY = "task_resource_intensity"
    TASK_COMPLETION_TIME_AND_STEPS = "task_completion_time_and_steps"
    INTERACTIVE_SERVICE_RESPONSIVENESS = "interactive_service_responsiveness"


class AccessEconomicsSubcomponent(StrEnum):
    PUBLIC_BENCHMARK_TASK_COST = "public_benchmark_task_cost"
    AGENTIC_TASK_COST = "agentic_task_cost"
    FIXED_TARIFF_BASKETS = "fixed_tariff_baskets"


class CostEvidenceKind(StrEnum):
    PROVIDER_BILLING_RECORD = "provider_billing_record"
    BENCHMARK_MEASURED_AND_CALCULATED = "benchmark_measured_and_calculated"
    TOKEN_TARIFF_MODEL = "token_tariff_model"
    FIXED_TARIFF_BASKET = "fixed_tariff_basket"
    SOURCE_REPORTED = "source_reported"
    UNKNOWN = "unknown"


class PublicOverallWeights(ConfigModel):
    capability: float = Field(gt=0)
    operational_efficiency: float = Field(gt=0)
    access_economics: float = Field(gt=0)

    @model_validator(mode="after")
    def sums_to_one(self) -> PublicOverallWeights:
        total = self.capability + self.operational_efficiency + self.access_economics
        if abs(total - 1.0) > 1e-9:
            raise ValueError("UMI Public overall weights must sum to 1")
        return self


class PublicWeightConfig(ConfigModel):
    capability_domains: dict[PublicDomain, float]
    operational_efficiency: dict[OperationalEfficiencySubcomponent, float]
    access_economics: dict[AccessEconomicsSubcomponent, float]
    overall: PublicOverallWeights

    @model_validator(mode="after")
    def validate_groups(self) -> PublicWeightConfig:
        for name, weights in (
            ("capability_domains", self.capability_domains),
            ("operational_efficiency", self.operational_efficiency),
            ("access_economics", self.access_economics),
        ):
            positive = all(value > 0 for value in weights.values())
            if not weights or abs(sum(weights.values()) - 1.0) > 1e-9 or not positive:
                raise ValueError(f"{name} weights must be positive and sum to 1")
        return self


class PublicEligibilityConfig(ConfigModel):
    required_common_core_coverage: float = Field(gt=0, le=1)
    minimum_anchor_panel: int = Field(ge=8)
    maximum_source_share: float = Field(gt=0, le=1)
    evidence_snapshot_cutoff: str = Field(min_length=1)
    maximum_evidence_age_days: int | None = Field(default=None, gt=0)


class PublicFamilyDefinition(ConfigModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    component: str = Field(pattern=r"^[a-z_]+$")
    parent: str = Field(min_length=1)
    weight: float = Field(gt=0, le=1)
    correlation_group: str = Field(min_length=1)
    source_organization: str = Field(min_length=1)


class CommonCoreSeries(ConfigModel):
    series_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    required_entity_ids: tuple[str, ...] = Field(min_length=1)
    anchor_panel_id: str = Field(min_length=1)
    correlation_group: str = Field(min_length=1)


class PublicEditionConfig(ConfigModel):
    edition_id: str
    formula_version: str
    normalization_version: str
    engine_version: str
    package_version: str
    policy_mode: str
    weights: PublicWeightConfig
    eligibility: PublicEligibilityConfig
    families: tuple[PublicFamilyDefinition, ...]
    common_core: tuple[CommonCoreSeries, ...]

    @model_validator(mode="after")
    def validate_edition(self) -> PublicEditionConfig:
        if self.edition_id not in PUBLIC_EDITION_IDS:
            raise ValueError(f"unknown public edition {self.edition_id}")
        expected_formula = PUBLIC_EDITION_IDS[self.edition_id]
        if self.formula_version != expected_formula:
            raise ValueError(f"{self.edition_id} formula must be {expected_formula}")
        if self.policy_mode != "public":
            raise ValueError("Public policy_mode must be public")
        family_ids = [item.id for item in self.families]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("public family IDs must be unique")
        known = set(family_ids)
        for series in self.common_core:
            if series.family_id not in known:
                raise ValueError(f"common-core series {series.series_id} references unknown family")
        return self


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected mapping: {path}")
    return raw


def edition_config_dir(edition: str, *, root: Path | None = None) -> Path:
    base = root or ROOT
    if edition == "v0.3":
        return base / "config"
    return base / "config" / "editions" / edition


def load_public_edition_config(
    path: Path | None = None,
    *,
    edition: str = "v0.4",
) -> PublicEditionConfig:
    directory = path or edition_config_dir(edition)
    edition_raw = _load_yaml(directory / "edition.yaml")
    weights = _load_yaml(directory / "weights.yaml")
    eligibility = _load_yaml(directory / "eligibility.yaml")
    families_raw = _load_yaml(directory / "families.yaml")
    core_raw = _load_yaml(directory / "common-core.yaml")
    payload = {
        **edition_raw,
        "weights": weights,
        "eligibility": eligibility,
        "families": families_raw["families"],
        "common_core": core_raw.get("series", ()),
    }
    return PublicEditionConfig.model_validate(payload)
