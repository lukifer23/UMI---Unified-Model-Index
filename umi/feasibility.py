"""Static edition feasibility: a policy must be able to meet its own gates."""

from __future__ import annotations

from collections import defaultdict

from umi.config import ProjectConfig
from umi.edition import (
    AccessEconomicsSubcomponent,
    OperationalEfficiencySubcomponent,
    PublicDomain,
    PublicEditionConfig,
)
from umi.schemas import WorkloadCategory


class FeasibilityError(ValueError):
    """The edition cannot theoretically satisfy its publication gates."""


def theoretical_legacy_workload_coverage(config: ProjectConfig) -> float:
    represented = {
        family.category
        for family in config.workload_families
        if family.weight > 0
    }
    return sum(
        weight
        for category, weight in config.weights.workload_weights.items()
        if category in represented
    )


def validate_legacy_edition_feasibility(config: ProjectConfig) -> None:
    """Legacy v0.3 is loadable, but is infeasible as a new Public edition."""
    maximum = theoretical_legacy_workload_coverage(config)
    efficiency_gate = config.eligibility.minimum_component_coverage["efficiency"]
    economics_gate = config.eligibility.minimum_component_coverage["economics"]
    workload_gate = config.eligibility.minimum_efficiency_workload_coverage
    errors: list[str] = []
    if maximum + 1e-12 < efficiency_gate:
        errors.append(
            f"operational_efficiency maximum attainable category coverage is {maximum:.2f}, "
            f"but publication threshold is {efficiency_gate:.2f}"
        )
    if maximum + 1e-12 < economics_gate:
        errors.append(
            f"economics maximum attainable category coverage is {maximum:.2f}, "
            f"but publication threshold is {economics_gate:.2f}"
        )
    if maximum + 1e-12 < workload_gate:
        errors.append(
            f"efficiency workload coverage maximum is {maximum:.2f}, "
            f"but publication threshold is {workload_gate:.2f}"
        )
    configured_categories = {item.category for item in config.workload_families}
    for category, weight in config.weights.workload_weights.items():
        if weight > 0 and category not in configured_categories:
            errors.append(
                f"positive-weight category {category.value} has no positive-weight family"
            )
    if errors:
        raise FeasibilityError(
            "edition v0.3 is infeasible as a Public edition: " + "; ".join(errors)
        )


def validate_public_edition_feasibility(config: PublicEditionConfig) -> None:
    parents_by_component: dict[str, set[str]] = defaultdict(set)
    for family in config.families:
        if family.weight > 0:
            parents_by_component[family.component].add(family.parent)

    required_parents: dict[str, tuple[str, ...]] = {
        "capability": tuple(item.value for item in config.weights.capability_domains),
        "operational_efficiency": tuple(
            item.value for item in config.weights.operational_efficiency
        ),
        "access_economics": tuple(item.value for item in config.weights.access_economics),
    }
    errors: list[str] = []
    for component, parents in required_parents.items():
        present = parents_by_component.get(component, set())
        for parent in parents:
            if parent not in present:
                errors.append(
                    f"positive-weight {component} parent {parent} has no positive-weight family"
                )
    family_ids = {item.id for item in config.families}
    for series in config.common_core:
        if series.family_id not in family_ids:
            errors.append(f"required series {series.series_id} has no family")
        if config.eligibility.minimum_anchor_panel < 8:
            errors.append("headline anchor panel minimum is below 8")
        if not series.required_entity_ids:
            errors.append(f"required series {series.series_id} lists no entities")
    if config.eligibility.required_common_core_coverage < 1.0 - 1e-12:
        errors.append("UMI Public required common-core coverage must be 1.0")
    if config.eligibility.maximum_source_share > 0.35 + 1e-12:
        errors.append("maximum_source_share exceeds the 0.35 Public cap")
    org_family_weight: dict[tuple[str, str], float] = defaultdict(float)
    parent_totals: dict[tuple[str, str], float] = defaultdict(float)
    for family in config.families:
        org_family_weight[(family.component, family.source_organization)] += family.weight
        parent_totals[(family.component, family.parent)] += family.weight
    component_org_share: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for family in config.families:
        parent_total = parent_totals[(family.component, family.parent)]
        if parent_total <= 0:
            continue
        parent_share = family.weight / parent_total
        if family.component == "capability":
            domain_weight = config.weights.capability_domains[PublicDomain(family.parent)]
            component_org_share[family.component][family.source_organization] += (
                domain_weight * parent_share
            )
        elif family.component == "operational_efficiency":
            sub_weight = config.weights.operational_efficiency[
                OperationalEfficiencySubcomponent(family.parent)
            ]
            component_org_share[family.component][family.source_organization] += (
                sub_weight * parent_share
            )
        elif family.component == "access_economics":
            sub_weight = config.weights.access_economics[
                AccessEconomicsSubcomponent(family.parent)
            ]
            component_org_share[family.component][family.source_organization] += (
                sub_weight * parent_share
            )
    cap = config.eligibility.maximum_source_share
    for component, shares in component_org_share.items():
        if len(shares) < 2:
            continue
        for organization, share in shares.items():
            if share > cap + 1e-12:
                errors.append(
                    f"{organization} would hold {share:.3f} of {component}, above cap {cap:.2f}"
                )
    if errors:
        raise FeasibilityError(
            f"edition {config.edition_id} is infeasible: " + "; ".join(errors)
        )


def unused_legacy_workload_categories(config: ProjectConfig) -> tuple[WorkloadCategory, ...]:
    represented = {family.category for family in config.workload_families}
    return tuple(
        category
        for category, weight in config.weights.workload_weights.items()
        if weight > 0 and category not in represented
    )
