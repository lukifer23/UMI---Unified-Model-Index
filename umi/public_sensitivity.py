"""Diagnostic Public weight hypotheses. Does not change the headline formula."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, TypedDict

from umi.edition import GOVERNED_EDITION_ID
from umi.public import ROOT


class WeightHypothesis(TypedDict):
    name: str
    capability: float
    operational_efficiency: float
    access_economics: float


WEIGHT_HYPOTHESES: tuple[WeightHypothesis, ...] = (
    {
        "name": "baseline",
        "capability": 0.55,
        "operational_efficiency": 0.25,
        "access_economics": 0.20,
    },
    {
        "name": "capability_60",
        "capability": 0.60,
        "operational_efficiency": 0.20,
        "access_economics": 0.20,
    },
    {
        "name": "operational_30",
        "capability": 0.50,
        "operational_efficiency": 0.30,
        "access_economics": 0.20,
    },
    {
        "name": "access_15",
        "capability": 0.60,
        "operational_efficiency": 0.25,
        "access_economics": 0.15,
    },
    {
        "name": "access_25",
        "capability": 0.50,
        "operational_efficiency": 0.25,
        "access_economics": 0.25,
    },
)


def _score(item: dict[str, Any], hypothesis: WeightHypothesis) -> float:
    return math.fsum(
        (
            hypothesis["capability"] * item["capability"],
            hypothesis["operational_efficiency"] * item["operational_efficiency"],
            hypothesis["access_economics"] * item["access_economics"],
        )
    )


def quantify_weight_sensitivity(
    payload: dict[str, Any] | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    scores = payload or json.loads(
        (ROOT / "data" / "editions" / edition_name / "processed" / "model-scores.json").read_text(
            encoding="utf-8"
        )
    )
    models = list(scores["models"])
    for hypothesis in WEIGHT_HYPOTHESES:
        total = math.fsum(
            (
                hypothesis["capability"],
                hypothesis["operational_efficiency"],
                hypothesis["access_economics"],
            )
        )
        if abs(total - 1.0) > 1e-12:
            raise ValueError(f"{hypothesis['name']} weights must sum to 1")
    scenarios: list[dict[str, Any]] = []
    baseline_order = [
        item["entity_id"]
        for item in sorted(models, key=lambda row: (-row["umi_public"], row["entity_id"]))
    ]
    ranges: dict[str, list[float]] = {item["entity_id"]: [] for item in models}
    for hypothesis in WEIGHT_HYPOTHESES:
        ranked = sorted(
            (
                {
                    "entity_id": item["entity_id"],
                    "diagnostic_public": _score(item, hypothesis),
                }
                for item in models
            ),
            key=lambda row: (-row["diagnostic_public"], row["entity_id"]),
        )
        order = [item["entity_id"] for item in ranked]
        for rank, item in enumerate(ranked, start=1):
            item["rank"] = rank
            ranges[item["entity_id"]].append(item["diagnostic_public"])
        scenarios.append(
            {
                "name": hypothesis["name"],
                "weights": {
                    "capability": hypothesis["capability"],
                    "operational_efficiency": hypothesis["operational_efficiency"],
                    "access_economics": hypothesis["access_economics"],
                },
                "order": order,
                "rank_changes": {
                    entity_id: baseline_order.index(entity_id) - order.index(entity_id)
                    for entity_id in baseline_order
                },
                "models": ranked,
            }
        )
    return {
        "edition_id": GOVERNED_EDITION_ID,
        "status": "diagnostic",
        "headline_unchanged": True,
        "hypotheses": [item["name"] for item in WEIGHT_HYPOTHESES],
        "scenarios": scenarios,
        "score_ranges": {
            entity_id: {
                "low": min(values),
                "high": max(values),
            }
            for entity_id, values in ranges.items()
        },
    }


def write_weight_sensitivity(
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    report = quantify_weight_sensitivity(edition_name=edition_name)
    (destination / "weight-sensitivity.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
