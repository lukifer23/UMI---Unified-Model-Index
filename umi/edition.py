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
EXPERIMENTAL_POINT_SCORE = "historical_experimental_point_score"
EXPERIMENTAL_POINT_SCORE_PUBLIC = "experimental_point_score"
PROVISIONAL_PUBLIC_SCORE = "provisional_public_score"
CERTIFIED_PUBLIC_SCORE = "certified_public_score"
GOVERNED_PUBLIC_INDEX = "governed_public_index"
SOURCE_CONCENTRATION_FAILED = "source_concentration_failed"
INSUFFICIENT_COMMON_SUPPORT = "insufficient_common_support"
IDENTITY_UNRESOLVED = "identity_unresolved"
UNCERTAINTY_INCOMPLETE = "uncertainty_incomplete"
EDITION_RELEASE_CLASSES = {
    PUBLIC_EDITION_ID: EXPERIMENTAL_POINT_SCORE,
    GOVERNED_EDITION_ID: PROVISIONAL_PUBLIC_SCORE,
}
V05_ANALYSIS_SURFACES = frozenset(
    {PROVISIONAL_PUBLIC_SCORE, CERTIFIED_PUBLIC_SCORE, GOVERNED_PUBLIC_INDEX}
)


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
    BENCHMARK_OBSERVED_COST = "benchmark_observed_cost"
    BENCHMARK_CALCULATED_COST = "benchmark_calculated_cost"
    BENCHMARK_MEASURED_AND_CALCULATED = "benchmark_measured_and_calculated"
    TOKEN_TARIFF_MODEL = "token_tariff_model"
    FIXED_TARIFF_BASKET = "fixed_tariff_basket"
    SOURCE_REPORTED = "source_reported"
    SOURCE_REPORTED_COST = "source_reported_cost"
    UNKNOWN = "unknown"


class SourceRole(StrEnum):
    BENCHMARK_OWNER = "benchmark_owner"
    EVALUATOR = "evaluator"
    RUN_EXECUTOR = "run_executor"
    DATA_DISTRIBUTOR = "data_distributor"
    PRICING_AUTHORITY = "pricing_authority"
    MODEL_DEVELOPER = "model_developer"


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


class PublicNormalizationConfig(ConfigModel):
    logit_eps: float = Field(gt=0, lt=0.1)
    winsor: float = Field(gt=0)
    high_effort_suffixes: tuple[str, ...] = Field(min_length=1)
    lower_transform: str = "neglog1p"
    iqr_scale: str = "legacy_mad_iqr"
    reject_out_of_range: bool = False
    duplicate_policy: str = "first_seen"
    excluded_config_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_suffixes(self) -> PublicNormalizationConfig:
        if any(not item.startswith("_") for item in self.high_effort_suffixes):
            raise ValueError("high-effort suffixes must start with _")
        if self.lower_transform not in {"neglog1p", "log"}:
            raise ValueError("lower_transform must be neglog1p or log")
        if self.iqr_scale not in {"legacy_mad_iqr", "iqr_over_1_349"}:
            raise ValueError("iqr_scale must be legacy_mad_iqr or iqr_over_1_349")
        if self.duplicate_policy not in {"first_seen", "declared"}:
            raise ValueError("duplicate_policy must be first_seen or declared")
        return self


class PublicFamilyDefinition(ConfigModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    component: str = Field(pattern=r"^[a-z_]+$")
    parent: str = Field(min_length=1)
    weight: float = Field(gt=0, le=1)
    correlation_group: str = Field(min_length=1)
    source_organization: str = Field(min_length=1)
    evaluator_organization: str | None = None
    run_executor_organization: str | None = None
    data_distributor: str | None = None
    benchmark_owner: str | None = None

    def concentration_origin(self) -> str:
        return (
            self.evaluator_organization
            or self.run_executor_organization
            or self.source_organization
        )


class CommonCoreSeries(ConfigModel):
    series_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    member: str = Field(min_length=1)
    field: str = Field(min_length=1)
    kind: str = Field(pattern=r"^(proportion|lower)$")
    required_entity_ids: tuple[str, ...] = Field(min_length=1)
    anchor_panel_id: str = Field(min_length=1)
    correlation_group: str = Field(min_length=1)
    harness: str | None = None
    panel_filter: str | None = None
    interval_field: str | None = None
    interval_kind: str | None = None
    ablate: bool = False
    evidence_kind: str = Field(min_length=1)
    success_adjusted: bool | None = None
    cost_evidence: str | None = None

    @model_validator(mode="after")
    def validate_extract_and_interval(self) -> CommonCoreSeries:
        if self.panel_filter not in {None, "high_effort"}:
            raise ValueError(f"{self.series_id} has an unsupported panel_filter")
        if (self.interval_field is None) != (self.interval_kind is None):
            raise ValueError(f"{self.series_id} interval_field and interval_kind must be paired")
        if self.interval_kind not in {None, "standard_error", "ci95_halfwidth"}:
            raise ValueError(f"{self.series_id} has an unsupported interval_kind")
        allowed_kinds = {
            "capability_measurement",
            "source_reported_resource_mean",
            "source_reported_task_cost",
        }
        if self.evidence_kind not in allowed_kinds:
            raise ValueError(f"{self.series_id} has an unsupported evidence_kind")
        if self.cost_evidence == CostEvidenceKind.PROVIDER_BILLING_RECORD.value:
            raise ValueError(f"{self.series_id} cannot treat public cost as provider billing")
        if self.success_adjusted is True:
            raise ValueError(
                f"{self.series_id} cannot claim success-adjusted resources "
                "without attempt residuals"
            )
        return self


class PublicEditionConfig(ConfigModel):
    edition_id: str
    formula_version: str
    normalization_version: str
    engine_version: str
    package_version: str
    policy_mode: str
    release_class: str
    comparison_profile_id: str | None = None
    weights: PublicWeightConfig
    eligibility: PublicEligibilityConfig
    normalization: PublicNormalizationConfig
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
        expected_class = EDITION_RELEASE_CLASSES[self.edition_id]
        if self.release_class != expected_class:
            raise ValueError(f"{self.edition_id} release_class must be {expected_class}")
        family_ids = [item.id for item in self.families]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("public family IDs must be unique")
        known = {item.id: item for item in self.families}
        series_ids = [item.series_id for item in self.common_core]
        if len(series_ids) != len(set(series_ids)):
            raise ValueError("public series IDs must be unique")
        used_families: set[str] = set()
        for series in self.common_core:
            family = known.get(series.family_id)
            if family is None:
                raise ValueError(f"common-core series {series.series_id} references unknown family")
            if series.correlation_group != family.correlation_group:
                raise ValueError(f"{series.series_id} correlation_group must match family")
            expected_kind = {
                "capability": "capability_measurement",
                "operational_efficiency": "source_reported_resource_mean",
                "access_economics": "source_reported_task_cost",
            }.get(family.component)
            if expected_kind is None:
                raise ValueError(f"{series.series_id} family has an unsupported component")
            if series.evidence_kind != expected_kind:
                raise ValueError(
                    f"{series.series_id} evidence_kind must be {expected_kind} "
                    f"for {family.component}"
                )
            if family.component == "access_economics":
                if series.cost_evidence != CostEvidenceKind.SOURCE_REPORTED.value:
                    raise ValueError(f"{series.series_id} Access cost must be source_reported")
                if series.success_adjusted is not False:
                    raise ValueError(f"{series.series_id} Access cost is not success-adjusted")
            elif family.component == "operational_efficiency":
                if series.cost_evidence is not None:
                    raise ValueError(f"{series.series_id} OpEff series cannot carry cost_evidence")
                if series.success_adjusted is not False:
                    raise ValueError(
                        f"{series.series_id} OpEff means are not success-adjusted"
                    )
            elif series.cost_evidence is not None or series.success_adjusted is not None:
                raise ValueError(
                    f"{series.series_id} capability series cannot carry cost semantics"
                )
            used_families.add(family.id)
        unused = set(known) - used_families
        if unused:
            raise ValueError("unused public families: " + ", ".join(sorted(unused)))
        parent_weights: dict[tuple[str, str], float] = {}
        for family in self.families:
            key = (family.component, family.parent)
            parent_weights[key] = parent_weights.get(key, 0.0) + family.weight
        for key, total in parent_weights.items():
            if abs(total - 1.0) > 1e-12:
                raise ValueError(f"{key[0]}/{key[1]} family weights must sum to 1")
        return self


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected mapping: {path}")
    return raw


def _config_search_roots(bundle_dir: Path | str | None = None) -> tuple[Path, ...]:
    here = Path(__file__).resolve()
    roots: list[Path] = []
    if bundle_dir is not None:
        roots.append(Path(bundle_dir))
    roots.extend(
        (
            Path.cwd(),
            here.parents[1],
            here.parent / "packaged_config",
        )
    )
    return tuple(roots)


def edition_config_dir(
    edition: str,
    *,
    root: Path | None = None,
    bundle_dir: Path | str | None = None,
) -> Path:
    if root is not None:
        base = root
        if edition == "v0.3":
            return base / "config"
        return base / "config" / "editions" / edition
    checked: list[Path] = []
    for base in _config_search_roots(bundle_dir):
        candidates: tuple[Path, ...]
        if edition == "v0.3":
            candidates = (base / "config",)
        else:
            candidates = (
                base / "config" / "editions" / edition,
                base / "editions" / edition,
            )
        for candidate in candidates:
            checked.append(candidate)
            marker = "weights.yaml" if edition == "v0.3" else "edition.yaml"
            if (candidate / marker).is_file():
                return candidate
    raise FileNotFoundError(
        f"public edition config for {edition} not found; searched "
        + ", ".join(str(item) for item in checked)
    )


def load_public_edition_config(
    path: Path | None = None,
    *,
    edition: str = "v0.4",
    bundle_dir: Path | str | None = None,
) -> PublicEditionConfig:
    directory = path or edition_config_dir(edition, bundle_dir=bundle_dir)
    edition_raw = _load_yaml(directory / "edition.yaml")
    weights = _load_yaml(directory / "weights.yaml")
    eligibility = _load_yaml(directory / "eligibility.yaml")
    normalization = _load_yaml(directory / "normalization.yaml")
    families_raw = _load_yaml(directory / "families.yaml")
    core_raw = _load_yaml(directory / "common-core.yaml")
    payload = {
        **edition_raw,
        "weights": weights,
        "eligibility": eligibility,
        "normalization": normalization,
        "families": families_raw["families"],
        "common_core": core_raw.get("series", ()),
    }
    return PublicEditionConfig.model_validate(payload)
