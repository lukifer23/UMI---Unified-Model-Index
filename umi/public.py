"""UMI Public v0.4 scoring from frozen public artifacts."""

from __future__ import annotations

import csv
import io
import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from umi.edition import PUBLIC_EDITION_ID, PublicEditionConfig, load_public_edition_config
from umi.identity import load_public_identities
from umi.version import ENGINE_VERSION, PACKAGE_VERSION

ROOT = Path(__file__).resolve().parents[1]
EPOCH_ZIP = ROOT / "data" / "sources" / "v0.3" / "epoch-benchmark-data-2026-08-14.zip"
PILOT_MAP = {
    "claude-opus-5_max": "claude-opus-5-max",
    "claude-fable-5_max": "claude-fable-5-max",
    "gpt-5.6-sol_max": "gpt-5.6-sol-max",
    "kimi-k3_max": "kimi-k3-max",
    "glm-5.2_max": "glm-5.2-max",
}
INCOMPLETE_COST = {"claude-fable-5_max"}
LOGIT_EPS = 1e-3
WINSOR = 3.0


@dataclass(frozen=True)
class SeriesPoint:
    config_id: str
    entity_id: str | None
    raw: float
    complete: bool


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _logit(value: float) -> float:
    clipped = min(max(value, LOGIT_EPS), 1.0 - LOGIT_EPS)
    return math.log(clipped / (1.0 - clipped))


def transform_proportion(raw: float) -> float:
    return _logit(raw)


def transform_lower_better(raw: float, offset: float = 1.0) -> float:
    return -math.log(raw + offset)


def robust_z(value: float, panel: tuple[float, ...]) -> tuple[float, float, float]:
    ordered = sorted(panel)
    mid = len(ordered) // 2
    median = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
    deviations = sorted(abs(item - median) for item in ordered)
    dmid = len(deviations) // 2
    mad = deviations[dmid] if len(deviations) % 2 else (deviations[dmid - 1] + deviations[dmid]) / 2
    sigma = 1.4826 * mad
    if sigma <= 1e-12:
        q1 = ordered[len(ordered) // 4]
        q3 = ordered[(3 * len(ordered)) // 4]
        iqr = q3 - q1
        sigma = 1.4826 * (iqr / 1.349) if iqr > 1e-12 else 0.0
    if sigma <= 1e-12:
        raise ValueError("anchor panel has no robust scale")
    z = (value - median) / sigma
    z = min(max(z, -WINSOR), WINSOR)
    return z, median, sigma


def series_score(raw: float, panel: tuple[float, ...], *, kind: str) -> dict[str, float]:
    transformed_panel = tuple(
        transform_proportion(item) if kind == "proportion" else transform_lower_better(item)
        for item in panel
    )
    transformed = (
        transform_proportion(raw) if kind == "proportion" else transform_lower_better(raw)
    )
    z, median, sigma = robust_z(transformed, transformed_panel)
    return {
        "raw": raw,
        "transformed": transformed,
        "robust_z": z,
        "score": 100.0 * _phi(z),
        "anchor_median": median,
        "anchor_sigma": sigma,
        "anchor_n": float(len(panel)),
    }


def load_deepswe_epoch_rows(path: Path = EPOCH_ZIP) -> tuple[dict[str, str], ...]:
    with zipfile.ZipFile(path) as archive:
        raw = archive.read("deepswe_external.csv").decode("utf-8")
    return tuple(csv.DictReader(io.StringIO(raw)))


def deepswe_points(field: str, *, require_complete_cost: bool = False) -> tuple[SeriesPoint, ...]:
    points: list[SeriesPoint] = []
    for row in load_deepswe_epoch_rows():
        if row.get("Harness") != "mini-swe-agent":
            continue
        raw_text = row.get(field, "")
        if raw_text in {"", None}:
            continue
        config_id = str(row["Model version"])
        complete = not (require_complete_cost and config_id in INCOMPLETE_COST)
        if require_complete_cost and not complete:
            continue
        points.append(
            SeriesPoint(
                config_id=config_id,
                entity_id=PILOT_MAP.get(config_id),
                raw=float(raw_text),
                complete=complete,
            )
        )
    return tuple(points)


def _pilot_scores(points: tuple[SeriesPoint, ...], kind: str) -> dict[str, dict[str, float]]:
    panel = tuple(item.raw for item in points)
    if len(panel) < 8:
        raise ValueError("anchor panel smaller than 8")
    scores: dict[str, dict[str, float]] = {}
    for item in points:
        if item.entity_id is None:
            continue
        scores[item.entity_id] = series_score(item.raw, panel, kind=kind)
    return scores


def score_public_edition(
    config: PublicEditionConfig | None = None,
) -> dict[str, Any]:
    edition = config or load_public_edition_config()
    identities = load_public_identities()
    capability = _pilot_scores(deepswe_points("Pass@1"), "proportion")
    resources = _pilot_scores(deepswe_points("Mean output tokens"), "lower")
    steps = _pilot_scores(deepswe_points("Mean agent steps"), "lower")
    cost_complete = deepswe_points("Mean cost (USD)", require_complete_cost=True)
    complete_entities = {item.entity_id for item in cost_complete if item.entity_id}
    missing_cost = sorted(set(PILOT_MAP.values()) - complete_entities)
    blockers = [
        {
            "missing_series": series,
            "affected_model": "all-five-common-core",
            "required_identity": "exact Max or documented composite",
            "sources_investigated": [
                "Epoch benchmark_data.zip live_bench_external.csv",
                "Epoch hle/gpqa/scicode/critpt external CSVs",
                "AA reviewed five-row extracts",
                "CursorBench five-row extract",
            ],
            "reason": (
                "No frozen public series has all five pilots and an 8+ same-harness "
                "anchor panel outside DeepSWE v1.1 mini-swe-agent."
            ),
            "resolving_evidence": (
                "A frozen same-harness extract with all five pilots plus 8+ anchors"
            ),
        }
        for series in (
            "general_reasoning_and_knowledge",
            "agentic_and_tool_mediated_work",
            "mathematics_and_science",
            "context_reliability_and_factual_discipline",
            "language_data_and_instruction_following",
            "interactive_service_responsiveness",
            "public_benchmark_task_cost",
            "fixed_tariff_baskets",
        )
    ]
    if missing_cost:
        blockers.append(
            {
                "missing_series": "deepswe-task-cost-complete",
                "affected_model": ",".join(missing_cost),
                "required_identity": "complete cost observation count",
                "sources_investigated": ["DeepSWE reviewed facts", "Epoch deepswe_external.csv"],
                "reason": (
                    "Fable DeepSWE cost is 432/436 and cannot enter a complete series"
                ),
                "resolving_evidence": (
                    "Complete Fable cost denominator or another all-five cost series"
                ),
            }
        )

    models: list[dict[str, Any]] = []
    for identity in identities:
        cap = capability.get(identity.entity_id)
        res = resources.get(identity.entity_id)
        step = steps.get(identity.entity_id)
        operational = None
        if res and step:
            operational = (
                0.45 / 0.75 * res["score"] + 0.30 / 0.75 * step["score"]
            )
        models.append(
            {
                "entity_id": identity.entity_id,
                "entity_kind": identity.entity_kind.value,
                "named_release": identity.named_release,
                "effort_setting": identity.effort_setting,
                "capability": cap["score"] if cap else None,
                "operational_efficiency": operational,
                "access_economics": None,
                "umi_public": None,
                "publication_state": "insufficient_common_support",
                "capability_series": {"deepswe-v1.1-pass1": cap},
                "operational_series": {
                    "deepswe-output-tokens": res,
                    "deepswe-agent-steps": step,
                },
            }
        )
    return {
        "edition_id": edition.edition_id,
        "formula_version": edition.formula_version,
        "normalization_version": edition.normalization_version,
        "engine_version": ENGINE_VERSION,
        "package_version": PACKAGE_VERSION,
        "comparison_profile_id": f"{PUBLIC_EDITION_ID}/deepswe-public-partial",
        "publication_state": "insufficient_common_support",
        "required_common_core_coverage": 0.0,
        "models": models,
        "blockers": blockers,
        "anchor_panel": {
            "id": "epoch-deepswe-v1.1-mini-swe-agent",
            "n": len(deepswe_points("Pass@1")),
            "source": "epoch-benchmark-data-2026-08-14.zip:deepswe_external.csv",
        },
    }


def write_public_artifacts(output_dir: Path | None = None) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / "v0.4" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    payload = score_public_edition()
    (destination / "model-scores.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "rejected-evidence.json").write_text(
        json.dumps({"blockers": payload["blockers"]}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
