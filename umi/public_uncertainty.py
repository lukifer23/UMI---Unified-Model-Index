"""Governed Public uncertainty from published source intervals and diagnostic ablation."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from umi.edition import (
    AccessEconomicsSubcomponent,
    ConfigModel,
    OperationalEfficiencySubcomponent,
    PublicDomain,
    load_public_edition_config,
)
from umi.identity import load_public_identities
from umi.public import (
    ROOT,
    entity_map_from_identities,
    epoch_points,
    load_epoch_member,
    public_series_specs,
    series_score,
)
from umi.public_crosswalk import config_id_for_entity

DRAW_COUNT = 2048
RESAMPLING_METHOD_VERSION = "umi-public-uncertainty-v0.5"


class PublicUncertaintyModelRow(ConfigModel):
    entity_id: str
    umi_public: float
    interval_low: float
    interval_high: float
    rank_low: int
    rank_high: int
    interval_status: str
    series_with_intervals: tuple[str, ...]
    series_without_intervals: tuple[str, ...]
    capability_low: float
    capability_high: float
    operational_efficiency_low: float
    operational_efficiency_high: float
    access_economics_low: float
    access_economics_high: float


class PublicFamilyAblation(ConfigModel):
    dropped_series: str
    order: tuple[str, ...]
    rank_changes: dict[str, int]


class PublicSourceAblation(ConfigModel):
    dropped_organization: str
    dropped_series: tuple[str, ...]
    emptied_domains: tuple[str, ...]
    remaining_capability_domains: tuple[str, ...]
    order: tuple[str, ...]
    rank_changes: dict[str, int]
    models: tuple[dict[str, Any], ...]


class PublicPairwiseDifference(ConfigModel):
    left: str
    right: str
    p_left_greater: float
    p_right_greater: float
    mean_difference: float
    difference_low: float
    difference_high: float
    difference_status: str


class PublicUncertaintyReport(ConfigModel):
    edition_id: str
    method: str
    resampling_method_version: str
    draws: int
    seed_source: str
    correlation_groups: tuple[str, ...]
    models: tuple[PublicUncertaintyModelRow, ...]
    family_ablations: tuple[PublicFamilyAblation, ...]
    source_ablations: tuple[PublicSourceAblation, ...]
    pairwise: tuple[PublicPairwiseDifference, ...]
    limitations: tuple[str, ...]


def _finite(raw_text: str | None) -> float | None:
    if raw_text is None or raw_text == "":
        return None
    try:
        value = float(raw_text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def _sigma_from_source(kind: str, value: float) -> float:
    if kind == "ci95_halfwidth":
        return value / 1.96
    return value


def series_intervals(*, edition_name: str = "v0.5") -> dict[str, dict[str, float]]:
    edition = load_public_edition_config(edition=edition_name)
    intervals: dict[str, dict[str, float]] = {}
    for series in edition.common_core:
        if series.interval_field is None or series.interval_kind is None:
            continue
        seen: set[str] = set()
        for row in load_epoch_member(series.member):
            if series.harness and row.get("Harness") != series.harness:
                continue
            config_id = str(row["Model version"])
            if config_id in seen:
                continue
            seen.add(config_id)
            width = _finite(row.get(series.interval_field))
            if width is None or width < 0:
                continue
            intervals.setdefault(series.series_id, {})[config_id] = _sigma_from_source(
                series.interval_kind,
                width,
            )
    return intervals


def _percentile(ordered: list[float], quantile: float) -> float:
    if not ordered:
        raise ValueError("percentile requires draws")
    return ordered[int(quantile * (len(ordered) - 1))]


def _ablation_series(edition_name: str) -> tuple[str, ...]:
    edition = load_public_edition_config(edition=edition_name)
    return tuple(item.series_id for item in edition.common_core if item.ablate)


def _series_meta(edition_name: str) -> dict[str, dict[str, str]]:
    edition = load_public_edition_config(edition=edition_name)
    families = {item.id: item for item in edition.families}
    return {
        series.series_id: {
            "component": families[series.family_id].component,
            "domain": families[series.family_id].parent,
            "source_organization": families[series.family_id].source_organization,
            "correlation_group": series.correlation_group,
        }
        for series in edition.common_core
    }


def _capability_series_by_org(edition_name: str) -> dict[str, tuple[str, ...]]:
    meta = _series_meta(edition_name)
    by_org: dict[str, list[str]] = {}
    for series_id, item in meta.items():
        if item["component"] != "capability":
            continue
        by_org.setdefault(item["source_organization"], []).append(series_id)
    return {org: tuple(ids) for org, ids in sorted(by_org.items())}


def _capability_domains(
    edition_name: str,
    *,
    dropped: frozenset[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    meta = _series_meta(edition_name)
    remaining: set[str] = set()
    emptied: set[str] = set()
    seen: set[str] = set()
    for series_id, item in meta.items():
        if item["component"] != "capability":
            continue
        seen.add(item["domain"])
        if series_id not in dropped:
            remaining.add(item["domain"])
    emptied = seen - remaining
    return tuple(sorted(emptied)), tuple(sorted(remaining))


def _combine(
    series_scores: dict[str, float],
    *,
    dropped: frozenset[str] = frozenset(),
    edition_name: str = "v0.5",
) -> dict[str, float]:
    edition = load_public_edition_config(edition=edition_name)
    specs = public_series_specs(edition)
    cap_parts: dict[str, float] = {}
    family_totals: dict[str, float] = {}
    for spec in specs:
        if spec["component"] != "capability" or spec["id"] in dropped:
            continue
        family_totals[spec["domain"]] = family_totals.get(spec["domain"], 0.0) + spec[
            "family_weight"
        ]
    for spec in specs:
        if spec["component"] != "capability" or spec["id"] in dropped:
            continue
        weight = spec["family_weight"] / family_totals[spec["domain"]]
        cap_parts[spec["domain"]] = cap_parts.get(spec["domain"], 0.0) + (
            weight * series_scores[spec["id"]]
        )
    if not cap_parts:
        raise ValueError("source ablation emptied Capability")
    domain_weights = edition.weights.capability_domains
    domain_total = math.fsum(domain_weights[PublicDomain(domain)] for domain in cap_parts)
    capability = math.fsum(
        (domain_weights[PublicDomain(domain)] / domain_total) * value
        for domain, value in sorted(cap_parts.items())
    )
    opeff = math.fsum(
        edition.weights.operational_efficiency[OperationalEfficiencySubcomponent(spec["domain"])]
        * series_scores[spec["id"]]
        for spec in specs
        if spec["component"] == "operational_efficiency"
    )
    access = math.fsum(
        edition.weights.access_economics[AccessEconomicsSubcomponent(spec["domain"])]
        * series_scores[spec["id"]]
        for spec in specs
        if spec["component"] == "access_economics"
    )
    public = math.fsum(
        (
            edition.weights.overall.capability * capability,
            edition.weights.overall.operational_efficiency * opeff,
            edition.weights.overall.access_economics * access,
        )
    )
    return {
        "capability": capability,
        "operational_efficiency": opeff,
        "access_economics": access,
        "umi_public": public,
    }


def _clip_raw(raw: float, kind: str) -> float:
    if kind == "proportion":
        return min(max(raw, 1e-6), 1.0 - 1e-6)
    return max(raw, 0.0)


def _rank_scenario(
    point_scores: dict[str, dict[str, float]],
    identities: tuple[Any, ...],
    baseline_order: list[str],
    dropped: frozenset[str],
    edition_name: str,
) -> tuple[list[str], dict[str, int], list[dict[str, Any]]]:
    scenario: list[tuple[str, float]] = []
    for identity in identities:
        combined = _combine(
            point_scores[identity.entity_id],
            dropped=dropped,
            edition_name=edition_name,
        )
        scenario.append((identity.entity_id, combined["umi_public"]))
    ranked = [
        entity_id
        for entity_id, _value in sorted(scenario, key=lambda pair: (-pair[1], pair[0]))
    ]
    by_score = dict(scenario)
    models = [
        {
            "entity_id": entity_id,
            "diagnostic_public": by_score[entity_id],
            "rank": index,
        }
        for index, entity_id in enumerate(ranked, start=1)
    ]
    rank_changes = {
        entity_id: ranked.index(entity_id) - baseline_order.index(entity_id)
        for entity_id in baseline_order
    }
    return ranked, rank_changes, models


def _pairwise_from_samples(
    samples: dict[str, list[float]], order: list[str]
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(order):
        for right in order[left_index + 1 :]:
            diffs = [
                samples[left][index] - samples[right][index]
                for index in range(len(samples[left]))
            ]
            ordered = sorted(diffs)
            n_draws = len(diffs)
            p_left = sum(1 for value in diffs if value > 0) / n_draws
            p_right = sum(1 for value in diffs if value < 0) / n_draws
            low = _percentile(ordered, 0.025)
            high = _percentile(ordered, 0.975)
            if low > 0:
                status = "left_greater"
            elif high < 0:
                status = "right_greater"
            else:
                status = "indistinguishable"
            pairs.append(
                {
                    "left": left,
                    "right": right,
                    "p_left_greater": p_left,
                    "p_right_greater": p_right,
                    "mean_difference": math.fsum(diffs) / n_draws,
                    "difference_low": low,
                    "difference_high": high,
                    "difference_status": status,
                }
            )
    return pairs


def quantify_public_uncertainty(
    payload: dict[str, Any],
    *,
    edition_name: str = "v0.5",
    draws: int = DRAW_COUNT,
    sigma_scale: float = 1.0,
) -> dict[str, Any]:
    if sigma_scale <= 0:
        raise ValueError("sigma_scale must be positive")
    identities = load_public_identities(edition=edition_name)
    edition = load_public_edition_config(edition=edition_name)
    specs = public_series_specs(edition)
    meta = _series_meta(edition_name)
    mapping = entity_map_from_identities(identities, edition=edition_name)
    intervals = series_intervals(edition_name=edition_name)
    panels: dict[str, tuple[float, ...]] = {}
    point_raw: dict[str, dict[str, float]] = {}
    point_scores: dict[str, dict[str, float]] = {}
    for spec in specs:
        points = epoch_points(
            spec["member"],
            spec["field"],
            require_harness=spec.get("harness"),
            panel_filter=spec.get("panel_filter"),
            identities=identities,
            entity_map=mapping,
            high_effort_suffixes=edition.normalization.high_effort_suffixes,
        )
        panels[spec["id"]] = tuple(item.raw for item in points)
        for item in points:
            if item.entity_id is None:
                continue
            point_raw.setdefault(item.entity_id, {})[spec["id"]] = item.raw
            point_scores.setdefault(item.entity_id, {})[spec["id"]] = series_score(
                item.raw,
                panels[spec["id"]],
                kind=spec["kind"],
                logit_eps=edition.normalization.logit_eps,
                winsor=edition.normalization.winsor,
            )["score"]
    seed = int(str(payload["scored_data_fingerprint"])[:16], 16)
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {item.entity_id: [] for item in identities}
    component_samples: dict[str, dict[str, list[float]]] = {
        item.entity_id: {
            "capability": [],
            "operational_efficiency": [],
            "access_economics": [],
        }
        for item in identities
    }
    for _ in range(draws):
        public_by_id: dict[str, float] = {}
        for identity in identities:
            config_id = config_id_for_entity(identity.entity_id, edition=edition_name)
            perturbed: dict[str, float] = {}
            group_z: dict[str, float] = {}
            for spec in specs:
                raw = point_raw[identity.entity_id][spec["id"]]
                sigma = intervals.get(spec["id"], {}).get(config_id)
                if sigma is not None and sigma > 0:
                    group = meta[spec["id"]]["correlation_group"]
                    if group not in group_z:
                        group_z[group] = rng.gauss(0.0, 1.0)
                    raw = _clip_raw(
                        raw + group_z[group] * sigma * sigma_scale,
                        spec["kind"],
                    )
                perturbed[spec["id"]] = series_score(
                    raw,
                    panels[spec["id"]],
                    kind=spec["kind"],
                    logit_eps=edition.normalization.logit_eps,
                    winsor=edition.normalization.winsor,
                )["score"]
            combined = _combine(perturbed, edition_name=edition_name)
            public_by_id[identity.entity_id] = combined["umi_public"]
            component_samples[identity.entity_id]["capability"].append(combined["capability"])
            component_samples[identity.entity_id]["operational_efficiency"].append(
                combined["operational_efficiency"]
            )
            component_samples[identity.entity_id]["access_economics"].append(
                combined["access_economics"]
            )
        for entity_id, value in public_by_id.items():
            samples[entity_id].append(value)
    models: list[dict[str, Any]] = []
    for item in payload["models"]:
        entity_id = item["entity_id"]
        ordered_draws = sorted(samples[entity_id])
        ranks = []
        for index in range(draws):
            ordered = sorted(
                ((other, samples[other][index]) for other in samples),
                key=lambda pair: (-pair[1], pair[0]),
            )
            ranks.append(next(i for i, pair in enumerate(ordered, start=1) if pair[0] == entity_id))
        covered = [
            spec["id"]
            for spec in specs
            if config_id_for_entity(entity_id, edition=edition_name)
            in intervals.get(spec["id"], {})
        ]
        cap = sorted(component_samples[entity_id]["capability"])
        opeff = sorted(component_samples[entity_id]["operational_efficiency"])
        access = sorted(component_samples[entity_id]["access_economics"])
        models.append(
            {
                "entity_id": entity_id,
                "umi_public": item["umi_public"],
                "interval_low": _percentile(ordered_draws, 0.025),
                "interval_high": _percentile(ordered_draws, 0.975),
                "rank_low": min(ranks),
                "rank_high": max(ranks),
                "interval_status": "partial_source_interval",
                "series_with_intervals": covered,
                "series_without_intervals": [
                    spec["id"] for spec in specs if spec["id"] not in covered
                ],
                "capability_low": _percentile(cap, 0.025),
                "capability_high": _percentile(cap, 0.975),
                "operational_efficiency_low": _percentile(opeff, 0.025),
                "operational_efficiency_high": _percentile(opeff, 0.975),
                "access_economics_low": _percentile(access, 0.025),
                "access_economics_high": _percentile(access, 0.975),
            }
        )
    baseline_order = [
        item["entity_id"]
        for item in sorted(payload["models"], key=lambda row: row["rank"])
    ]
    family_ablations: list[dict[str, Any]] = []
    for dropped in _ablation_series(edition_name):
        ranked, rank_changes, _models = _rank_scenario(
            point_scores,
            identities,
            baseline_order,
            frozenset({dropped}),
            edition_name,
        )
        family_ablations.append(
            {
                "dropped_series": dropped,
                "order": ranked,
                "rank_changes": rank_changes,
            }
        )
    source_ablations: list[dict[str, Any]] = []
    for organization, series_ids in _capability_series_by_org(edition_name).items():
        dropped_ids = frozenset(series_ids)
        emptied, remaining = _capability_domains(edition_name, dropped=dropped_ids)
        ranked, rank_changes, scenario_models = _rank_scenario(
            point_scores,
            identities,
            baseline_order,
            dropped_ids,
            edition_name,
        )
        source_ablations.append(
            {
                "dropped_organization": organization,
                "dropped_series": series_ids,
                "emptied_domains": emptied,
                "remaining_capability_domains": remaining,
                "order": ranked,
                "rank_changes": rank_changes,
                "models": scenario_models,
            }
        )
    report = {
        "edition_id": payload["edition_id"],
        "method": "source_interval_monte_carlo_plus_family_and_source_ablation",
        "resampling_method_version": RESAMPLING_METHOD_VERSION,
        "draws": draws,
        "seed_source": "scored_data_fingerprint",
        "correlation_groups": tuple(
            sorted({item["correlation_group"] for item in meta.values()})
        ),
        "models": models,
        "family_ablations": family_ablations,
        "source_ablations": source_ablations,
        "pairwise": _pairwise_from_samples(samples, baseline_order),
        "limitations": (
            "Intervals use published stderr or CI half-width where the frozen extract has them.",
            "SciCode, CritPt, DeepSWE tokens/steps, and WeirdML cost stay at their point values.",
            "Series in one correlation group share a residual when both have published intervals.",
            "Source-organization ablation drops Capability series only and is diagnostic.",
            "This is not an attempt-level hierarchical bootstrap.",
        ),
    }
    return PublicUncertaintyReport.model_validate(report).model_dump(mode="json")


def write_public_uncertainty(
    payload: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.5",
    draws: int = DRAW_COUNT,
) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    scores = payload or json.loads(
        (destination / "model-scores.json").read_text(encoding="utf-8")
    )
    report = quantify_public_uncertainty(scores, edition_name=edition_name, draws=draws)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "uncertainty.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
