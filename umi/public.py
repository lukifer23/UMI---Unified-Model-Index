"""UMI Public v0.4 scoring from frozen public artifacts."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from umi.edition import (
    V05_ANALYSIS_SURFACES,
    PublicEditionConfig,
    PublicNormalizationConfig,
    load_public_edition_config,
)
from umi.feasibility import validate_public_edition_feasibility
from umi.identity import PublicSystemIdentity, evidence_matches_entity, load_public_identities
from umi.public_crosswalk import entity_map_from_crosswalk
from umi.public_eligibility import decide_public_eligibility
from umi.public_paths import DEFAULT_EPOCH_ZIP, REPO_ROOT, resolve_epoch_zip

ROOT = REPO_ROOT
EPOCH_ZIP = DEFAULT_EPOCH_ZIP


def entity_map_from_identities(
    identities: tuple[PublicSystemIdentity, ...],
    *,
    edition: str,
) -> dict[str, str]:
    return entity_map_from_crosswalk(identities, edition=edition)
INCOMPLETE_COST = {"claude-fable-5_max"}
HIGH_EFFORT_SUFFIXES = ("_max", "_xhigh", "_high", "_promax")
LOGIT_EPS = 1e-3
WINSOR = 3.0


class SeriesSpec(TypedDict):
    id: str
    member: str
    field: str
    kind: str
    component: str
    domain: str
    family_weight: float
    anchor_panel_id: str
    harness: NotRequired[str]
    panel_filter: NotRequired[str]


@dataclass(frozen=True)
class SeriesPoint:
    config_id: str
    entity_id: str | None
    raw: float
    complete: bool
    source_name: str
    source_row_id: str | None = None


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _logit(value: float, eps: float = LOGIT_EPS) -> float:
    clipped = min(max(value, eps), 1.0 - eps)
    return math.log(clipped / (1.0 - clipped))


def transform_proportion(
    raw: float,
    eps: float = LOGIT_EPS,
    *,
    reject_out_of_range: bool = False,
) -> float:
    if reject_out_of_range and (raw < 0.0 or raw > 1.0):
        raise ValueError(f"proportion {raw} is outside [0, 1]")
    return _logit(raw, eps)


def transform_lower_better(
    raw: float,
    offset: float = 1.0,
    *,
    mode: str = "neglog1p",
) -> float:
    if mode == "log":
        if raw <= 0.0:
            raise ValueError(f"log transform requires raw > 0, got {raw}")
        return -math.log(raw)
    return -math.log(raw + offset)


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


def _composite_from_row(row: dict[str, str]) -> tuple[bool, tuple[str, ...]]:
    blob = f"{row.get('Name', '')} {row.get('Notes', '')}".lower()
    if "fallback" in blob or "opus 4.8" in blob:
        return True, ("claude-opus-4.8",)
    return False, ()


def _source_effort(row: dict[str, str], config_id: str) -> str | None:
    del config_id
    effort = str(row.get("Reasoning effort") or "").strip()
    return effort or None


def robust_z(
    value: float,
    panel: tuple[float, ...],
    *,
    winsor: float = WINSOR,
    iqr_scale: str = "legacy_mad_iqr",
) -> tuple[float, float, float]:
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
        if iqr <= 1e-12:
            sigma = 0.0
        elif iqr_scale == "iqr_over_1_349":
            sigma = iqr / 1.349
        else:
            sigma = 1.4826 * (iqr / 1.349)
    if sigma <= 1e-12:
        raise ValueError("anchor panel has no robust scale")
    z = (value - median) / sigma
    z = min(max(z, -winsor), winsor)
    return z, median, sigma


def _transform_raw(
    raw: float,
    *,
    kind: str,
    logit_eps: float,
    lower_transform: str,
    reject_out_of_range: bool,
) -> float:
    if kind == "proportion":
        return transform_proportion(
            raw, logit_eps, reject_out_of_range=reject_out_of_range
        )
    return transform_lower_better(raw, mode=lower_transform)


def series_score(
    raw: float,
    panel: tuple[float, ...],
    *,
    kind: str,
    logit_eps: float = LOGIT_EPS,
    winsor: float = WINSOR,
    lower_transform: str = "neglog1p",
    iqr_scale: str = "legacy_mad_iqr",
    reject_out_of_range: bool = False,
) -> dict[str, float]:
    transformed_panel = tuple(
        _transform_raw(
            item,
            kind=kind,
            logit_eps=logit_eps,
            lower_transform=lower_transform,
            reject_out_of_range=reject_out_of_range,
        )
        for item in panel
    )
    transformed = _transform_raw(
        raw,
        kind=kind,
        logit_eps=logit_eps,
        lower_transform=lower_transform,
        reject_out_of_range=reject_out_of_range,
    )
    z, median, sigma = robust_z(
        transformed, transformed_panel, winsor=winsor, iqr_scale=iqr_scale
    )
    return {
        "raw": raw,
        "transformed": transformed,
        "robust_z": z,
        "score": 100.0 * _phi(z),
        "anchor_median": median,
        "anchor_sigma": sigma,
        "anchor_n": float(len(panel)),
    }


def load_epoch_member(
    member: str,
    zip_path: Path | None = None,
) -> tuple[dict[str, str], ...]:
    archive_path = zip_path if zip_path is not None else resolve_epoch_zip()
    with zipfile.ZipFile(archive_path) as archive:
        raw = archive.read(member).decode("utf-8")
    return tuple(csv.DictReader(io.StringIO(raw)))


def load_deepswe_epoch_rows(path: Path | None = None) -> tuple[dict[str, str], ...]:
    return load_epoch_member("deepswe_external.csv", zip_path=path or resolve_epoch_zip())


def epoch_points(
    member: str,
    field: str,
    *,
    zip_path: Path | None = None,
    require_harness: str | None = None,
    skip_incomplete_cost: bool = False,
    identities: tuple[PublicSystemIdentity, ...] | None = None,
    panel_filter: str | None = None,
    entity_map: dict[str, str] | None = None,
    high_effort_suffixes: tuple[str, ...] = HIGH_EFFORT_SUFFIXES,
    duplicate_policy: str = "first_seen",
    excluded_config_ids: tuple[str, ...] = (),
) -> tuple[SeriesPoint, ...]:
    known = {item.entity_id: item for item in identities} if identities is not None else None
    mapping = entity_map if entity_map is not None else {}
    excluded = set(excluded_config_ids)
    seen: dict[str, float] = {}
    points: list[SeriesPoint] = []
    for index, row in enumerate(load_epoch_member(member, zip_path=zip_path)):
        if require_harness and row.get("Harness") != require_harness:
            continue
        raw_value = _finite(row.get(field))
        if raw_value is None:
            continue
        config_id = str(row["Model version"])
        if config_id in excluded:
            continue
        if panel_filter == "high_effort" and not config_id.endswith(high_effort_suffixes):
            continue
        if config_id in seen:
            if abs(seen[config_id] - raw_value) <= 1e-15:
                continue
            if duplicate_policy == "first_seen":
                continue
            raise ValueError(
                f"{member} has conflicting values for {config_id}: "
                f"{seen[config_id]} vs {raw_value}"
            )
        if skip_incomplete_cost and config_id in INCOMPLETE_COST:
            continue
        seen[config_id] = raw_value
        entity_id = mapping.get(config_id)
        if entity_id is not None and known is not None:
            identity = known[entity_id]
            composite, fallbacks = _composite_from_row(row)
            accepted, _reason = evidence_matches_entity(
                entity=identity,
                source_effort=_source_effort(row, config_id),
                source_is_composite=composite,
                source_fallbacks=fallbacks,
                reviewed_crosswalk_effort=identity.effort_setting if entity_map else None,
            )
            if not accepted:
                entity_id = None
        source_row_id = str(row.get("id") or "").strip() or f"{member}:{index}"
        points.append(
            SeriesPoint(
                config_id=config_id,
                entity_id=entity_id,
                raw=raw_value,
                complete=config_id not in INCOMPLETE_COST,
                source_name=str(row.get("Name") or ""),
                source_row_id=source_row_id,
            )
        )
    return tuple(points)


def deepswe_points(
    field: str,
    *,
    zip_path: Path | None = None,
    require_complete_cost: bool = False,
) -> tuple[SeriesPoint, ...]:
    return epoch_points(
        "deepswe_external.csv",
        field,
        zip_path=zip_path,
        require_harness="mini-swe-agent",
        skip_incomplete_cost=require_complete_cost,
    )


def series_score_kwargs(normalization: PublicNormalizationConfig) -> dict[str, Any]:
    return {
        "logit_eps": normalization.logit_eps,
        "winsor": normalization.winsor,
        "lower_transform": normalization.lower_transform,
        "iqr_scale": normalization.iqr_scale,
        "reject_out_of_range": normalization.reject_out_of_range,
    }


def _pilot_scores(
    points: tuple[SeriesPoint, ...],
    scale: Any,
) -> dict[str, dict[str, float]]:
    from umi.public_scale import PublicScoreScale, apply_public_scale

    if not isinstance(scale, PublicScoreScale):
        raise TypeError("public scoring requires a PublicScoreScale")
    if len(points) != scale.n:
        raise ValueError(f"{scale.series_id} panel n drifted from the named scale")
    scores: dict[str, dict[str, float]] = {}
    for item in points:
        if item.entity_id is None:
            continue
        scores[item.entity_id] = apply_public_scale(item.raw, scale)
    return scores


def public_series_specs(edition: PublicEditionConfig) -> tuple[SeriesSpec, ...]:
    families = {item.id: item for item in edition.families}
    specs: list[SeriesSpec] = []
    for series in edition.common_core:
        family = families[series.family_id]
        spec: SeriesSpec = {
            "id": series.series_id,
            "member": series.member,
            "field": series.field,
            "kind": series.kind,
            "component": family.component,
            "domain": family.parent,
            "family_weight": family.weight,
            "anchor_panel_id": series.anchor_panel_id,
        }
        if series.harness:
            spec["harness"] = series.harness
        if series.panel_filter:
            spec["panel_filter"] = series.panel_filter
        specs.append(spec)
    return tuple(specs)


def _digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _weighted_sum(parts: list[tuple[float, float]]) -> float:
    return math.fsum(weight * value for weight, value in parts)


def _diagnostic_blockers(*, zip_path: Path | None = None) -> tuple[dict[str, Any], ...]:
    complete_cost = deepswe_points(
        "Mean cost (USD)", zip_path=zip_path, require_complete_cost=True
    )
    complete_ids = {item.entity_id for item in complete_cost if item.entity_id}
    return (
        {
            "affected_model": "claude-fable-5-max",
            "missing_series": "deepswe-mean-cost",
            "reason": (
                "Official DeepSWE v1.1 cost is observed on 432 of 436 scored Fable attempts "
                "and cannot enter a complete all-attempt Access series"
            ),
            "required_identity": "complete cost observation count",
            "resolving_evidence": (
                "Complete Fable cost denominator or another all-five billed/calculated series"
            ),
            "sources_investigated": [
                "DeepSWE reviewed facts",
                "Epoch deepswe_external.csv",
            ],
            "complete_cost_entity_ids": sorted(complete_ids),
        },
        {
            "affected_model": "edition-scope",
            "missing_series": "context_reliability_and_factual_discipline",
            "reason": (
                "No frozen public series has all five exact Max identities and an 8+ same-harness "
                "anchor panel for context reliability"
            ),
            "required_identity": "exact Max or documented composite",
            "resolving_evidence": (
                "A frozen same-harness extract with all five pilots plus 8+ anchors"
            ),
            "sources_investigated": [
                "Epoch simpleqa_verified.csv (missing claude-fable-5_max)",
                "AA five-row extracts (anchor n=5)",
            ],
        },
        {
            "affected_model": "edition-scope",
            "missing_series": "language_data_and_instruction_following",
            "reason": (
                "No frozen public series has all five exact Max identities and an 8+ same-harness "
                "anchor panel for language, data, or instruction following"
            ),
            "required_identity": "exact Max or documented composite",
            "resolving_evidence": (
                "A frozen same-harness extract with all five pilots plus 8+ anchors"
            ),
            "sources_investigated": [
                "Epoch live_bench_external.csv (zero 2026 Max pilots)",
                "AA five-row extracts (anchor n=5)",
            ],
        },
    )


def score_public_bundle(
    bundle: Any,
    *,
    edition: PublicEditionConfig | None = None,
    identities: tuple[PublicSystemIdentity, ...] | None = None,
    zip_path: Path | None = None,
) -> dict[str, Any]:
    """Production public scorer. Scores only a revalidated PublicScoringBundle."""
    from umi.public_bundle import PublicScoringBundle, bundle_points
    from umi.public_scale import build_public_panels_and_scales

    if not isinstance(bundle, PublicScoringBundle):
        raise TypeError("production public scoring requires a PublicScoringBundle")
    edition_name = "v0.5" if bundle.edition_id.endswith("v0.5") else "v0.4"
    loaded_edition = edition or load_public_edition_config(edition=edition_name)
    validate_public_edition_feasibility(loaded_edition)
    eligibility = decide_public_eligibility(loaded_edition)
    loaded = identities or load_public_identities(edition=edition_name)
    identities = loaded
    if set(bundle.entity_ids) != {item.entity_id for item in identities}:
        raise ValueError("bundle entity_ids do not match the identity manifest")
    from umi.public_certificate import EPOCH_SHA256

    if bundle.source_artifact_sha256 != EPOCH_SHA256:
        raise ValueError("bundle zip checksum does not match the registry")
    edition = loaded_edition
    domain_weights = {
        item.value: weight for item, weight in edition.weights.capability_domains.items()
    }
    opeff_weights = {
        item.value: weight for item, weight in edition.weights.operational_efficiency.items()
    }
    access_weights = {
        item.value: weight for item, weight in edition.weights.access_economics.items()
    }
    families = {item.id: item for item in edition.families}
    access_cost_evidence = next(
        series.cost_evidence
        for series in edition.common_core
        if families[series.family_id].component == "access_economics"
    )
    if access_cost_evidence != "source_reported":
        raise ValueError("public Access cost_evidence must be source_reported")
    specs = public_series_specs(edition)
    _panels, scales = build_public_panels_and_scales(bundle, edition)
    scale_by_series = {item.series_id: item for item in scales}
    scored_series: dict[str, dict[str, dict[str, float]]] = {}
    anchors: dict[str, dict[str, Any]] = {}
    for spec in specs:
        points = bundle_points(bundle, spec["id"])
        scored_series[spec["id"]] = _pilot_scores(points, scale_by_series[spec["id"]])
        anchors[spec["id"]] = {
            "member": spec["member"],
            "field": spec["field"],
            "kind": spec["kind"],
            "n": len(points),
            "panel_filter": spec.get("panel_filter"),
            "source": f"epoch-benchmark-data-2026-08-14.zip:{spec['member']}",
        }

    models: list[dict[str, Any]] = []
    for identity in identities:
        cap_parts: dict[str, float] = {}
        capability_series: dict[str, dict[str, float]] = {}
        for spec in specs:
            if spec["component"] != "capability":
                continue
            detail = scored_series[spec["id"]][identity.entity_id]
            capability_series[spec["id"]] = detail
            cap_parts[spec["domain"]] = cap_parts.get(spec["domain"], 0.0) + (
                spec["family_weight"] * detail["score"]
            )
        capability = _weighted_sum(
            [(domain_weights[domain], value) for domain, value in sorted(cap_parts.items())]
        )
        operational_series: dict[str, dict[str, float]] = {}
        opeff_parts: list[tuple[float, float]] = []
        for spec in specs:
            if spec["component"] != "operational_efficiency":
                continue
            detail = scored_series[spec["id"]][identity.entity_id]
            operational_series[spec["id"]] = detail
            opeff_parts.append((opeff_weights[spec["domain"]], detail["score"]))
        opeff = _weighted_sum(opeff_parts)
        access_series: dict[str, dict[str, float]] = {}
        access_parts: list[tuple[float, float]] = []
        for spec in specs:
            if spec["component"] != "access_economics":
                continue
            detail = scored_series[spec["id"]][identity.entity_id]
            access_series[spec["id"]] = detail
            access_parts.append((access_weights[spec["domain"]], detail["score"]))
        access = _weighted_sum(access_parts)
        public = _weighted_sum(
            [
                (edition.weights.overall.capability, capability),
                (edition.weights.overall.operational_efficiency, opeff),
                (edition.weights.overall.access_economics, access),
            ]
        )
        if not all(math.isfinite(value) for value in (capability, opeff, access, public)):
            raise ValueError(f"non-finite public score for {identity.entity_id}")
        models.append(
            {
                "entity_id": identity.entity_id,
                "entity_kind": identity.entity_kind.value,
                "named_release": identity.named_release,
                "effort_setting": identity.effort_setting,
                "capability": capability,
                "operational_efficiency": opeff,
                "access_economics": access,
                "umi_public": public,
                "publication_state": eligibility.publication_state,
                "cost_evidence": access_cost_evidence,
                "capability_series": capability_series,
                "operational_series": operational_series,
                "access_series": access_series,
            }
        )
    ranked = sorted(models, key=lambda item: (-item["umi_public"], item["entity_id"]))
    for index, item in enumerate(ranked, start=1):
        item["point_order"] = index
        item["rank"] = index
        item["rank_low"] = index
        item["rank_high"] = index
        item["tie_group"] = None
        item["rank_status"] = "point_order_only"
    fingerprint = _digest(
        {
            "edition_id": edition.edition_id,
            "formula_version": edition.formula_version,
            "normalization_version": edition.normalization_version,
            "series": [spec["id"] for spec in specs],
            "weights": edition.weights.model_dump(mode="json"),
            "models": [
                {
                    "entity_id": item["entity_id"],
                    "capability": item["capability"],
                    "operational_efficiency": item["operational_efficiency"],
                    "access_economics": item["access_economics"],
                    "umi_public": item["umi_public"],
                    "capability_series": {
                        series_id: detail["raw"]
                        for series_id, detail in item["capability_series"].items()
                    },
                    "operational_series": {
                        series_id: detail["raw"]
                        for series_id, detail in item["operational_series"].items()
                    },
                    "access_series": {
                        series_id: detail["raw"]
                        for series_id, detail in item["access_series"].items()
                    },
                }
                for item in sorted(models, key=lambda row: row["entity_id"])
            ],
        }
    )
    return {
        "edition_id": edition.edition_id,
        "formula_version": edition.formula_version,
        "normalization_version": edition.normalization_version,
        "engine_version": edition.engine_version,
        "package_version": edition.package_version,
        "comparison_profile_id": f"{edition.edition_id}/frozen-epoch-common-core",
        "publication_state": eligibility.publication_state,
        "certified": eligibility.certified,
        "eligibility": eligibility.model_dump(mode="json"),
        "required_common_core_coverage": 1.0,
        "scored_data_fingerprint": fingerprint,
        "models": models,
        "blockers": _diagnostic_blockers(zip_path=zip_path),
        "series": [spec["id"] for spec in specs],
        "anchors": anchors,
        "strict_ranks": False,
        "anchor_panel_fingerprints": {
            panel.panel_id: panel.panel_fingerprint
            for panel in _panels
        },
    }


def score_public_edition(
    config: PublicEditionConfig | None = None,
    *,
    edition_name: str = "v0.4",
    identities: tuple[PublicSystemIdentity, ...] | None = None,
    bundle_dir: Path | str | None = None,
    zip_path: Path | None = None,
) -> dict[str, Any]:
    from umi.public_bundle import load_public_scoring_bundle

    edition = config or load_public_edition_config(edition=edition_name)
    loaded = identities or load_public_identities(edition=edition_name)
    bundle = load_public_scoring_bundle(
        edition_name=edition_name,
        config=edition,
        identities=loaded,
        bundle_dir=bundle_dir,
        zip_path=zip_path,
    )
    return score_public_bundle(
        bundle,
        edition=edition,
        identities=loaded,
        zip_path=zip_path or (resolve_epoch_zip(bundle_dir) if bundle_dir else None),
    )


def write_public_artifacts(
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.4",
    bundle_dir: Path | str | None = None,
) -> dict[str, Any]:
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    payload = score_public_edition(edition_name=edition_name, bundle_dir=bundle_dir)
    frozen_v04 = ROOT / "data" / "editions" / "v0.4" / "processed"
    if edition_name == "v0.4" and destination.resolve() == frozen_v04.resolve():
        return payload
    (destination / "model-scores.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "rejected-evidence.json").write_text(
        json.dumps({"blockers": payload["blockers"]}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (destination / "common-core.json").write_text(
        json.dumps(
            {
                "edition_id": payload["edition_id"],
                "series": payload["series"],
                "anchors": payload["anchors"],
                "required_common_core_coverage": payload["required_common_core_coverage"],
                "scored_data_fingerprint": payload["scored_data_fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    edition = load_public_edition_config(edition=edition_name)
    if edition.release_class in V05_ANALYSIS_SURFACES:
        from umi.public_bundle import load_public_scoring_bundle, write_public_scoring_bundle
        from umi.public_candidates import write_candidate_audits
        from umi.public_certificate import build_public_certificate
        from umi.public_governance import write_governance_artifacts
        from umi.public_uncertainty import quantify_public_uncertainty
        from umi.public_validate import validate_public_scores

        validation = validate_public_scores(payload, edition_name=edition_name)
        if not validation["valid"]:
            raise ValueError("v0.5 validation failed: " + "; ".join(validation["errors"]))
        uncertainty = quantify_public_uncertainty(payload, edition_name=edition_name)
        from umi.public_uncertainty import attach_interval_ranks

        attach_interval_ranks(payload["models"], uncertainty)
        (destination / "validation.json").write_text(
            json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (destination / "uncertainty.json").write_text(
            json.dumps(uncertainty, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        certificate = build_public_certificate(payload, validation, uncertainty)
        (destination / "public-index-certificate.json").write_text(
            json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        scored_bundle = load_public_scoring_bundle(edition_name=edition_name)
        write_public_scoring_bundle(
            scored_bundle,
            destination,
            edition_name=edition_name,
        )
        from umi.public_scale import write_public_panels_and_scales

        write_public_panels_and_scales(
            scored_bundle,
            edition,
            destination,
            edition_name=edition_name,
        )
        candidate_audits = write_candidate_audits(destination)
        governance = write_governance_artifacts(destination, edition_name=edition_name)
        payload = {
            **payload,
            "validation": validation,
            "uncertainty": uncertainty,
            "certificate": certificate,
            "candidate_audits": candidate_audits,
            "governance": governance,
        }
    from analysis.public_dashboard import write_public_dashboard

    write_public_dashboard(payload, destination)
    return payload
