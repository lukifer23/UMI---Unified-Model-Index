from __future__ import annotations

import pytest

from umi.config import load_project_config
from umi.edition import load_public_edition_config
from umi.feasibility import (
    FeasibilityError,
    theoretical_legacy_workload_coverage,
    unused_legacy_workload_categories,
    validate_legacy_edition_feasibility,
    validate_public_edition_feasibility,
)


def test_legacy_v03_is_infeasible_as_a_public_edition() -> None:
    config = load_project_config("config")
    assert theoretical_legacy_workload_coverage(config) == pytest.approx(0.35)
    unused = {item.value for item in unused_legacy_workload_categories(config)}
    assert unused == {
        "research_analysis",
        "tool_use_agents",
        "browser_computer_use",
        "long_horizon",
    }
    with pytest.raises(FeasibilityError, match="0.35"):
        validate_legacy_edition_feasibility(config)


def test_single_source_cap_makes_an_edition_infeasible() -> None:
    config = load_public_edition_config()
    payload = config.model_dump(mode="json")
    for family in payload["families"]:
        if family["component"] == "capability" and family["id"] != "epoch-weirdml":
            family["source_organization"] = "one-lab"
    with pytest.raises(FeasibilityError, match="above cap"):
        validate_public_edition_feasibility(type(config).model_validate(payload))


def test_v04_public_policy_is_statically_feasible() -> None:
    config = load_public_edition_config()
    validate_public_edition_feasibility(config)
    assert config.weights.overall.capability == pytest.approx(0.55)
    assert config.weights.overall.operational_efficiency == pytest.approx(0.25)
    assert config.weights.overall.access_economics == pytest.approx(0.20)
    assert config.eligibility.required_common_core_coverage == pytest.approx(1.0)
    assert config.eligibility.maximum_source_share == pytest.approx(0.35)
    assert config.eligibility.minimum_anchor_panel == 8
    assert abs(sum(config.weights.capability_domains.values()) - 1.0) < 1e-12
    assert "public_benchmark_task_cost" in {
        item.value for item in config.weights.access_economics
    }
