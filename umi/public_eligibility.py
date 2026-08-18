"""Single eligibility path for public validate/score/build/certificate."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import Field

from umi.edition import (
    CERTIFIED_PUBLIC_SCORE,
    EXPERIMENTAL_POINT_SCORE_PUBLIC,
    PROVISIONAL_PUBLIC_SCORE,
    SOURCE_CONCENTRATION_FAILED,
    ConfigModel,
    PublicEditionConfig,
    PublicFamilyDefinition,
)


class PublicEligibilityDecision(ConfigModel):
    eligible: bool
    publication_state: str
    certified: bool
    reason_codes: tuple[str, ...]
    details: dict[str, Any] = Field(default_factory=dict)


def _origin(family: PublicFamilyDefinition) -> str:
    return family.concentration_origin()


def component_source_shares(edition: PublicEditionConfig) -> dict[str, dict[str, float]]:
    capability = {item.value: weight for item, weight in edition.weights.capability_domains.items()}
    operational = {
        item.value: weight for item, weight in edition.weights.operational_efficiency.items()
    }
    access = {item.value: weight for item, weight in edition.weights.access_economics.items()}
    domain_weights = {
        "capability": capability,
        "operational_efficiency": operational,
        "access_economics": access,
    }
    shares: dict[str, dict[str, float]] = {
        "capability": defaultdict(float),
        "operational_efficiency": defaultdict(float),
        "access_economics": defaultdict(float),
    }
    for family in edition.families:
        parent_weight = domain_weights[family.component][family.parent]
        shares[family.component][_origin(family)] += family.weight * parent_weight
    return {component: dict(values) for component, values in shares.items()}


def source_hhi(shares: dict[str, float]) -> float:
    return sum(value * value for value in shares.values())


def decide_public_eligibility(edition: PublicEditionConfig) -> PublicEligibilityDecision:
    reasons: list[str] = []
    details: dict[str, Any] = {}
    shares = component_source_shares(edition)
    cap = edition.eligibility.maximum_source_share
    concentration: dict[str, Any] = {}
    for component, orgs in shares.items():
        largest = max(orgs.values()) if orgs else 0.0
        concentration[component] = {
            "source_shares": orgs,
            "maximum_source_share": cap,
            "cap_applied": True,
            "largest_share": largest,
            "source_count": len(orgs),
            "source_HHI": source_hhi(orgs),
        }
        if largest - cap > 1e-12:
            reasons.append(SOURCE_CONCENTRATION_FAILED)
            details[f"{component}_largest_share"] = largest
    details["source_concentration"] = concentration

    present_parents = {
        (family.component, family.parent) for family in edition.families if family.weight > 0
    }
    required = {
        ("capability", "context_reliability_and_factual_discipline"),
        ("capability", "language_data_and_instruction_following"),
        ("operational_efficiency", "interactive_service_responsiveness"),
        ("access_economics", "agentic_task_cost"),
        ("access_economics", "fixed_tariff_baskets"),
    }
    missing = sorted(parent for parent in required if parent not in present_parents)
    if missing:
        reasons.append("construct_incomplete")
        details["missing_construct_parents"] = [f"{item[0]}/{item[1]}" for item in missing]

    unadjusted = [
        series.series_id
        for series in edition.common_core
        if series.success_adjusted is False
        and series.evidence_kind
        in {"source_reported_resource_mean", "source_reported_task_cost"}
    ]
    if unadjusted:
        reasons.append("success_adjustment_unavailable")
        details["unadjusted_series"] = unadjusted

    unique_reasons = tuple(dict.fromkeys(reasons))
    certified = not unique_reasons
    if certified:
        state = CERTIFIED_PUBLIC_SCORE
    elif SOURCE_CONCENTRATION_FAILED in unique_reasons or "construct_incomplete" in unique_reasons:
        state = PROVISIONAL_PUBLIC_SCORE
    else:
        state = EXPERIMENTAL_POINT_SCORE_PUBLIC
    if edition.edition_id.endswith("v0.4"):
        state = EXPERIMENTAL_POINT_SCORE_PUBLIC
    return PublicEligibilityDecision(
        eligible=certified,
        publication_state=state,
        certified=certified,
        reason_codes=unique_reasons,
        details=details,
    )
