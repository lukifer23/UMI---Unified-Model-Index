"""Governed Public uncertainty from published source intervals and family ablation."""

from __future__ import annotations

import math
import random
from typing import Any

from umi.edition import (
    AccessEconomicsSubcomponent,
    OperationalEfficiencySubcomponent,
    PublicDomain,
    load_public_edition_config,
)
from umi.identity import load_public_identities
from umi.public import (
    SERIES,
    config_id_for_entity,
    entity_map_from_identities,
    epoch_points,
    load_epoch_member,
    series_score,
)

UNCERTAINTY_FIELDS = {
    "epoch-chess-puzzles": ("stderr", "standard_error"),
    "epoch-gpqa": ("stderr", "standard_error"),
    "epoch-otis-aime": ("stderr", "standard_error"),
    "deepswe-v1.1-pass1": ("95% CI half-width", "ci95_halfwidth"),
    "epoch-weirdml": ("Accuracy SE", "standard_error"),
}
DRAW_COUNT = 2048
FAMILY_ABLATIONS = (
    "deepswe-v1.1-pass1",
    "epoch-scicode",
    "epoch-gpqa",
    "epoch-otis-aime",
    "epoch-critpt",
)


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


def series_intervals() -> dict[str, dict[str, float]]:
    intervals: dict[str, dict[str, float]] = {}
    for spec in SERIES:
        field_info = UNCERTAINTY_FIELDS.get(spec["id"])
        if field_info is None:
            continue
        field, kind = field_info
        seen: set[str] = set()
        for row in load_epoch_member(spec["member"]):
            if spec.get("harness") and row.get("Harness") != spec.get("harness"):
                continue
            config_id = str(row["Model version"])
            if config_id in seen:
                continue
            seen.add(config_id)
            width = _finite(row.get(field))
            if width is None or width < 0:
                continue
            intervals.setdefault(spec["id"], {})[config_id] = _sigma_from_source(kind, width)
    return intervals


def _combine(
    series_scores: dict[str, float],
    *,
    dropped: str | None = None,
    edition_name: str = "v0.5",
) -> dict[str, float]:
    edition = load_public_edition_config(edition=edition_name)
    cap_parts: dict[str, float] = {}
    family_totals: dict[str, float] = {}
    for spec in SERIES:
        if spec["component"] != "capability" or spec["id"] == dropped:
            continue
        family_totals[spec["domain"]] = family_totals.get(spec["domain"], 0.0) + spec[
            "family_weight"
        ]
    for spec in SERIES:
        if spec["component"] != "capability" or spec["id"] == dropped:
            continue
        weight = spec["family_weight"] / family_totals[spec["domain"]]
        cap_parts[spec["domain"]] = cap_parts.get(spec["domain"], 0.0) + (
            weight * series_scores[spec["id"]]
        )
    capability = math.fsum(
        edition.weights.capability_domains[PublicDomain(domain)] * value
        for domain, value in sorted(cap_parts.items())
    )
    opeff = math.fsum(
        edition.weights.operational_efficiency[OperationalEfficiencySubcomponent(spec["domain"])]
        * series_scores[spec["id"]]
        for spec in SERIES
        if spec["component"] == "operational_efficiency"
    )
    access = math.fsum(
        edition.weights.access_economics[AccessEconomicsSubcomponent(spec["domain"])]
        * series_scores[spec["id"]]
        for spec in SERIES
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


def quantify_public_uncertainty(
    payload: dict[str, Any],
    *,
    edition_name: str = "v0.5",
    draws: int = DRAW_COUNT,
) -> dict[str, Any]:
    identities = load_public_identities(edition=edition_name)
    mapping = entity_map_from_identities(identities)
    intervals = series_intervals()
    panels: dict[str, tuple[float, ...]] = {}
    point_raw: dict[str, dict[str, float]] = {}
    point_scores: dict[str, dict[str, float]] = {}
    for spec in SERIES:
        points = epoch_points(
            spec["member"],
            spec["field"],
            require_harness=spec.get("harness"),
            panel_filter=spec.get("panel_filter"),
            identities=identities,
            entity_map=mapping,
        )
        panels[spec["id"]] = tuple(item.raw for item in points)
        for item in points:
            if item.entity_id is None:
                continue
            point_raw.setdefault(item.entity_id, {})[spec["id"]] = item.raw
            point_scores.setdefault(item.entity_id, {})[spec["id"]] = series_score(
                item.raw, panels[spec["id"]], kind=spec["kind"]
            )["score"]
    seed = int(str(payload["scored_data_fingerprint"])[:16], 16)
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {item.entity_id: [] for item in identities}
    for _ in range(draws):
        public_by_id: dict[str, float] = {}
        for identity in identities:
            config_id = config_id_for_entity(identity.entity_id)
            perturbed: dict[str, float] = {}
            for spec in SERIES:
                raw = point_raw[identity.entity_id][spec["id"]]
                sigma = intervals.get(spec["id"], {}).get(config_id)
                if sigma is not None and sigma > 0:
                    raw = _clip_raw(raw + rng.gauss(0.0, sigma), spec["kind"])
                perturbed[spec["id"]] = series_score(
                    raw, panels[spec["id"]], kind=spec["kind"]
                )["score"]
            public_by_id[identity.entity_id] = _combine(
                perturbed, edition_name=edition_name
            )["umi_public"]
        for entity_id, value in public_by_id.items():
            samples[entity_id].append(value)
    models: list[dict[str, Any]] = []
    for item in payload["models"]:
        entity_id = item["entity_id"]
        ordered_draws = sorted(samples[entity_id])
        low = ordered_draws[int(0.025 * (len(ordered_draws) - 1))]
        high = ordered_draws[int(0.975 * (len(ordered_draws) - 1))]
        ranks = []
        for index in range(draws):
            ordered = sorted(
                ((other, samples[other][index]) for other in samples),
                key=lambda pair: (-pair[1], pair[0]),
            )
            ranks.append(next(i for i, pair in enumerate(ordered, start=1) if pair[0] == entity_id))
        covered = [
            spec["id"]
            for spec in SERIES
            if config_id_for_entity(entity_id) in intervals.get(spec["id"], {})
        ]
        models.append(
            {
                "entity_id": entity_id,
                "umi_public": item["umi_public"],
                "interval_low": low,
                "interval_high": high,
                "rank_low": min(ranks),
                "rank_high": max(ranks),
                "interval_status": "partial_source_interval",
                "series_with_intervals": covered,
                "series_without_intervals": [
                    spec["id"] for spec in SERIES if spec["id"] not in covered
                ],
            }
        )
    ablations: list[dict[str, Any]] = []
    baseline_order = [
        item["entity_id"]
        for item in sorted(payload["models"], key=lambda row: row["rank"])
    ]
    for dropped in FAMILY_ABLATIONS:
        scenario = []
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
        ablations.append(
            {
                "dropped_series": dropped,
                "order": ranked,
                "rank_changes": {
                    entity_id: ranked.index(entity_id) - baseline_order.index(entity_id)
                    for entity_id in baseline_order
                },
            }
        )
    return {
        "edition_id": payload["edition_id"],
        "method": "source_interval_monte_carlo_plus_family_ablation",
        "draws": draws,
        "seed_source": "scored_data_fingerprint",
        "models": models,
        "family_ablations": ablations,
        "limitations": (
            "Intervals use published stderr or CI half-width where the frozen extract has them.",
            "SciCode, CritPt, DeepSWE tokens/steps, and WeirdML cost stay at their point values.",
            "This is not an attempt-level hierarchical bootstrap.",
        ),
    }
