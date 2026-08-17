"""Diagnostic Public source ablation and rank-stability packaging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from umi.edition import GOVERNED_EDITION_ID, ConfigModel, load_public_edition_config
from umi.public import ROOT
from umi.public_certificate import overlapping_pairs
from umi.public_sensitivity import quantify_weight_sensitivity
from umi.public_uncertainty import quantify_public_uncertainty

ABLATION_METHOD = "capability_family_and_source_organization_ablation"
STABILITY_METHOD = "partial_interval_ranks_plus_ablation_and_weight_hypotheses"


class PublicCannotAblate(ConfigModel):
    source_organization: str
    component: str
    reason: str


class PublicSourceAblationReport(ConfigModel):
    edition_id: str
    status: str
    headline_unchanged: bool
    method: str
    family_ablations: tuple[dict[str, Any], ...]
    source_ablations: tuple[dict[str, Any], ...]
    cannot_ablate: tuple[PublicCannotAblate, ...]
    score_ranges: dict[str, dict[str, float]]
    limitations: tuple[str, ...]


class PublicRankStabilityModel(ConfigModel):
    entity_id: str
    published_rank: int
    umi_public: float
    interval_rank_low: int
    interval_rank_high: int
    family_ablation_rank_low: int
    family_ablation_rank_high: int
    source_ablation_rank_low: int
    source_ablation_rank_high: int
    weight_rank_low: int
    weight_rank_high: int
    interval_stable: bool
    diagnostically_stable: bool
    indistinguishable_from: tuple[str, ...]
    source_ablation_score_low: float
    source_ablation_score_high: float
    weight_score_low: float
    weight_score_high: float


class PublicRankStabilityReport(ConfigModel):
    edition_id: str
    status: str
    headline_unchanged: bool
    method: str
    models: tuple[PublicRankStabilityModel, ...]
    interval_stable_prefix: tuple[str, ...]
    overlap_cluster: tuple[str, ...]
    limitations: tuple[str, ...]


def _cannot_ablate(edition_name: str) -> tuple[dict[str, str], ...]:
    edition = load_public_edition_config(edition=edition_name)
    component_orgs: dict[str, set[str]] = {}
    for family in edition.families:
        component_orgs.setdefault(family.component, set()).add(family.source_organization)
    rows: list[dict[str, str]] = []
    for component, orgs in sorted(component_orgs.items()):
        if component == "capability" or len(orgs) != 1:
            continue
        organization = next(iter(orgs))
        label = (
            "Operational Efficiency"
            if component == "operational_efficiency"
            else "Access Economics"
        )
        rows.append(
            {
                "source_organization": organization,
                "component": component,
                "reason": (
                    f"single-origin component; dropping {organization} empties {label}"
                ),
            }
        )
    return tuple(rows)


def _score_ranges(uncertainty: dict[str, Any]) -> dict[str, dict[str, float]]:
    ranges: dict[str, list[float]] = {}
    for scenario in uncertainty["source_ablations"]:
        for item in scenario["models"]:
            ranges.setdefault(str(item["entity_id"]), []).append(float(item["diagnostic_public"]))
    return {
        entity_id: {"low": min(values), "high": max(values)}
        for entity_id, values in ranges.items()
    }


def quantify_source_ablation(
    payload: dict[str, Any] | None = None,
    uncertainty: dict[str, Any] | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    scores = payload or json.loads(
        (ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json").read_text(
            encoding="utf-8"
        )
    )
    report = uncertainty or quantify_public_uncertainty(scores, edition_name=edition_name)
    output = {
        "edition_id": GOVERNED_EDITION_ID,
        "status": "diagnostic",
        "headline_unchanged": True,
        "method": ABLATION_METHOD,
        "family_ablations": report["family_ablations"],
        "source_ablations": report["source_ablations"],
        "cannot_ablate": _cannot_ablate(edition_name),
        "score_ranges": _score_ranges(report),
        "limitations": (
            "Family and source-organization ablations are diagnostic and do not change umi_public.",
            "Only Capability series are dropped.",
            "Operational Efficiency and Access Economics are single-origin and cannot be removed "
            "without emptying a required headline component.",
            "Empty Capability domains are dropped and remaining domain weights are renormalized.",
            "The remaining series after a drop are not a valid headline common core.",
        ),
    }
    return PublicSourceAblationReport.model_validate(output).model_dump(mode="json")


def _ranks_from_orders(orders: list[list[str]], entity_id: str) -> tuple[int, int]:
    ranks = [order.index(entity_id) + 1 for order in orders]
    return min(ranks), max(ranks)


def quantify_rank_stability(
    payload: dict[str, Any] | None = None,
    uncertainty: dict[str, Any] | None = None,
    ablation: dict[str, Any] | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    scores = payload or json.loads(
        (ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json").read_text(
            encoding="utf-8"
        )
    )
    intervals = uncertainty or quantify_public_uncertainty(scores, edition_name=edition_name)
    source_ablation = ablation or quantify_source_ablation(
        scores, intervals, edition_name=edition_name
    )
    weights = quantify_weight_sensitivity(scores, edition_name=edition_name)
    published = sorted(scores["models"], key=lambda row: row["rank"])
    interval_by_id = {item["entity_id"]: item for item in intervals["models"]}
    family_orders = [list(item["order"]) for item in source_ablation["family_ablations"]]
    source_orders = [list(item["order"]) for item in source_ablation["source_ablations"]]
    weight_orders = [list(item["order"]) for item in weights["scenarios"]]
    overlap = overlapping_pairs(
        [
            {
                "entity_id": item["entity_id"],
                "interval_low": interval_by_id[item["entity_id"]]["interval_low"],
                "interval_high": interval_by_id[item["entity_id"]]["interval_high"],
            }
            for item in published
        ]
    )
    neighbors: dict[str, list[str]] = {item["entity_id"]: [] for item in published}
    for left, right in overlap:
        neighbors[left].append(right)
        neighbors[right].append(left)
    models: list[dict[str, Any]] = []
    for item in published:
        entity_id = item["entity_id"]
        interval = interval_by_id[entity_id]
        family_low, family_high = _ranks_from_orders(family_orders, entity_id)
        source_low, source_high = _ranks_from_orders(source_orders, entity_id)
        weight_low, weight_high = _ranks_from_orders(weight_orders, entity_id)
        published_rank = int(item["rank"])
        interval_stable = (
            interval["rank_low"] == published_rank and interval["rank_high"] == published_rank
        )
        diagnostically_stable = (
            interval_stable
            and family_low == family_high == published_rank
            and source_low == source_high == published_rank
            and weight_low == weight_high == published_rank
        )
        ablation_range = source_ablation["score_ranges"][entity_id]
        weight_range = weights["score_ranges"][entity_id]
        models.append(
            {
                "entity_id": entity_id,
                "published_rank": published_rank,
                "umi_public": item["umi_public"],
                "interval_rank_low": interval["rank_low"],
                "interval_rank_high": interval["rank_high"],
                "family_ablation_rank_low": family_low,
                "family_ablation_rank_high": family_high,
                "source_ablation_rank_low": source_low,
                "source_ablation_rank_high": source_high,
                "weight_rank_low": weight_low,
                "weight_rank_high": weight_high,
                "interval_stable": interval_stable,
                "diagnostically_stable": diagnostically_stable,
                "indistinguishable_from": tuple(sorted(neighbors[entity_id])),
                "source_ablation_score_low": ablation_range["low"],
                "source_ablation_score_high": ablation_range["high"],
                "weight_score_low": weight_range["low"],
                "weight_score_high": weight_range["high"],
            }
        )
    prefix: list[str] = []
    for item in models:
        if not item["interval_stable"]:
            break
        prefix.append(item["entity_id"])
    overlap_cluster = tuple(
        item["entity_id"] for item in models if item["indistinguishable_from"]
    )
    output = {
        "edition_id": GOVERNED_EDITION_ID,
        "status": "diagnostic",
        "headline_unchanged": True,
        "method": STABILITY_METHOD,
        "models": models,
        "interval_stable_prefix": tuple(prefix),
        "overlap_cluster": overlap_cluster,
        "limitations": (
            "Interval-stable ranks come from the partial source-interval Monte Carlo only.",
            "Family ablation, source-organization ablation, and weight hypotheses are diagnostic.",
            "Overlapping partial intervals remain indistinguishable on the certificate.",
            "This is not an attempt-level hierarchical bootstrap.",
        ),
    }
    return PublicRankStabilityReport.model_validate(output).model_dump(mode="json")


def write_rank_stability_artifacts(
    output_dir: Path | None = None,
    payload: dict[str, Any] | None = None,
    uncertainty: dict[str, Any] | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    scores = payload or json.loads(
        (destination / "model-scores.json").read_text(encoding="utf-8")
    )
    intervals = uncertainty or quantify_public_uncertainty(scores, edition_name=edition_name)
    ablation = quantify_source_ablation(scores, intervals, edition_name=edition_name)
    stability = quantify_rank_stability(
        scores, intervals, ablation, edition_name=edition_name
    )
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "source-ablation.json").write_text(
        json.dumps(ablation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "rank-stability.json").write_text(
        json.dumps(stability, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "source_ablation": ablation,
        "rank_stability": stability,
    }
