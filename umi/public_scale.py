"""Named Public anchor panels and stable score scales."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from umi.edition import V05_ANALYSIS_SURFACES, ConfigModel, PublicEditionConfig
from umi.public import (
    ROOT,
    _phi,
    _transform_raw,
    robust_z,
)
from umi.public_bundle import PublicScoringBundle, bundle_points
from umi.public_certificate import EPOCH_SHA256

TRANSFORM_NAMES = {"proportion": "logit", "neglog1p": "neglog1p", "log": "neglog"}


class PublicAnchorMember(ConfigModel):
    anchor_member_id: str
    source_row_id: str
    source_model_id: str
    entity_id: str | None = None
    raw_value: float
    transformed_value: float
    included: bool = True
    exclusion_reason: str | None = None


class PublicAnchorPanel(ConfigModel):
    panel_id: str
    member: str
    harness: str | None = None
    panel_filter: str | None = None
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    series_ids: tuple[str, ...]
    config_ids: tuple[str, ...]
    members: tuple[PublicAnchorMember, ...] = ()
    n: int = Field(ge=8)
    panel_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def bind_membership(self) -> PublicAnchorPanel:
        if self.n != len(self.config_ids):
            raise ValueError(f"{self.panel_id} n does not match config_ids")
        if len(self.config_ids) != len(set(self.config_ids)):
            raise ValueError(f"{self.panel_id} config_ids must be unique")
        return self


class PublicScoreScale(ConfigModel):
    scale_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    panel_id: str
    series_id: str
    kind: str
    transform: str
    logit_eps: float | None = None
    lower_transform: str = "neglog1p"
    iqr_scale: str = "legacy_mad_iqr"
    reject_out_of_range: bool = False
    winsor: float
    median: float
    sigma: float
    n: int = Field(ge=8)
    formula_version: str
    normalization_version: str


class PublicAnchorPanelSet(ConfigModel):
    edition_id: str
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    panels: tuple[PublicAnchorPanel, ...]


class PublicScoreScaleSet(ConfigModel):
    edition_id: str
    formula_version: str
    normalization_version: str
    scales: tuple[PublicScoreScale, ...]


def _digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def apply_public_scale(
    raw: float,
    scale: PublicScoreScale,
) -> dict[str, float]:
    if scale.kind == "proportion" and scale.logit_eps is None:
        raise ValueError(f"{scale.series_id} proportion scale missing logit_eps")
    transformed = _transform_raw(
        raw,
        kind=scale.kind,
        logit_eps=scale.logit_eps or 1e-3,
        lower_transform=scale.lower_transform,
        reject_out_of_range=scale.reject_out_of_range,
    )
    z = (transformed - scale.median) / scale.sigma
    z = min(max(z, -scale.winsor), scale.winsor)
    return {
        "raw": raw,
        "transformed": transformed,
        "robust_z": z,
        "score": 100.0 * _phi(z),
        "anchor_median": scale.median,
        "anchor_sigma": scale.sigma,
        "anchor_n": float(scale.n),
    }


def build_public_panels_and_scales(
    bundle: PublicScoringBundle,
    edition: PublicEditionConfig,
) -> tuple[tuple[PublicAnchorPanel, ...], tuple[PublicScoreScale, ...]]:
    series_by_panel: dict[str, list[str]] = {}
    membership: dict[str, tuple[str, ...]] = {}
    extract: dict[str, tuple[str, str | None, str | None]] = {}
    members_by_panel: dict[str, tuple[PublicAnchorMember, ...]] = {}
    for series in edition.common_core:
        contract = next(item for item in bundle.series if item.series_id == series.series_id)
        config_ids = tuple(sorted(item.config_id for item in contract.records))
        panel_id = series.anchor_panel_id
        series_by_panel.setdefault(panel_id, []).append(series.series_id)
        if panel_id in membership and membership[panel_id] != config_ids:
            raise ValueError(f"{panel_id} has inconsistent config membership")
        membership[panel_id] = config_ids
        extract[panel_id] = (series.member, series.harness, series.panel_filter)
        if panel_id not in members_by_panel:
            members_by_panel[panel_id] = tuple(
                PublicAnchorMember(
                    anchor_member_id=f"{panel_id}:{item.config_id}",
                    source_row_id=item.source_row_id or item.config_id,
                    source_model_id=item.config_id,
                    entity_id=item.entity_id,
                    raw_value=item.raw,
                    transformed_value=_transform_raw(
                        item.raw,
                        kind=series.kind,
                        logit_eps=edition.normalization.logit_eps,
                        lower_transform=edition.normalization.lower_transform,
                        reject_out_of_range=edition.normalization.reject_out_of_range,
                    ),
                )
                for item in sorted(contract.records, key=lambda row: row.config_id)
            )
    panels: list[PublicAnchorPanel] = []
    for panel_id, config_ids in sorted(membership.items()):
        member, harness, panel_filter = extract[panel_id]
        members = members_by_panel[panel_id]
        unsigned = {
            "panel_id": panel_id,
            "member": member,
            "harness": harness,
            "panel_filter": panel_filter,
            "source_artifact_sha256": bundle.source_artifact_sha256,
            "config_ids": config_ids,
            "members": [
                {
                    "source_row_id": item.source_row_id,
                    "source_model_id": item.source_model_id,
                    "raw_value": item.raw_value,
                    "transformed_value": item.transformed_value,
                }
                for item in members
            ],
        }
        panels.append(
            PublicAnchorPanel(
                panel_id=panel_id,
                member=member,
                harness=harness,
                panel_filter=panel_filter,
                source_artifact_sha256=bundle.source_artifact_sha256,
                series_ids=tuple(series_by_panel[panel_id]),
                config_ids=config_ids,
                members=members,
                n=len(config_ids),
                panel_fingerprint=_digest(unsigned),
            )
        )
    scales: list[PublicScoreScale] = []
    by_panel = {item.panel_id: item for item in panels}
    for series in edition.common_core:
        points = bundle_points(bundle, series.series_id)
        raws = tuple(item.raw for item in points)
        transformed_panel = tuple(
            _transform_raw(
                item,
                kind=series.kind,
                logit_eps=edition.normalization.logit_eps,
                lower_transform=edition.normalization.lower_transform,
                reject_out_of_range=edition.normalization.reject_out_of_range,
            )
            for item in raws
        )
        _z, median, sigma = robust_z(
            transformed_panel[0],
            transformed_panel,
            winsor=edition.normalization.winsor,
            iqr_scale=edition.normalization.iqr_scale,
        )
        transform_name = (
            "logit" if series.kind == "proportion" else edition.normalization.lower_transform
        )
        unsigned_scale = {
            "panel_id": series.anchor_panel_id,
            "series_id": series.series_id,
            "kind": series.kind,
            "transform": transform_name,
            "logit_eps": edition.normalization.logit_eps if series.kind == "proportion" else None,
            "lower_transform": edition.normalization.lower_transform,
            "iqr_scale": edition.normalization.iqr_scale,
            "winsor": edition.normalization.winsor,
            "median": median,
            "sigma": sigma,
            "n": len(raws),
            "formula_version": edition.formula_version,
            "normalization_version": edition.normalization_version,
            "panel_fingerprint": by_panel[series.anchor_panel_id].panel_fingerprint,
        }
        scales.append(
            PublicScoreScale(
                scale_id=_digest(unsigned_scale),
                panel_id=series.anchor_panel_id,
                series_id=series.series_id,
                kind=series.kind,
                transform=transform_name,
                logit_eps=(
                    edition.normalization.logit_eps if series.kind == "proportion" else None
                ),
                lower_transform=edition.normalization.lower_transform,
                iqr_scale=edition.normalization.iqr_scale,
                reject_out_of_range=edition.normalization.reject_out_of_range,
                winsor=edition.normalization.winsor,
                median=median,
                sigma=sigma,
                n=len(raws),
                formula_version=edition.formula_version,
                normalization_version=edition.normalization_version,
            )
        )
    return tuple(panels), tuple(scales)


def write_public_panels_and_scales(
    bundle: PublicScoringBundle,
    edition: PublicEditionConfig,
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    if edition.release_class not in V05_ANALYSIS_SURFACES:
        raise ValueError("public panels and scales are a governed-index surface")
    if bundle.source_artifact_sha256 != EPOCH_SHA256:
        raise ValueError("panel zip checksum does not match the registry")
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    panels, scales = build_public_panels_and_scales(bundle, edition)
    panel_set = PublicAnchorPanelSet(
        edition_id=edition.edition_id,
        source_artifact_sha256=bundle.source_artifact_sha256,
        panels=panels,
    ).model_dump(mode="json")
    scale_set = PublicScoreScaleSet(
        edition_id=edition.edition_id,
        formula_version=edition.formula_version,
        normalization_version=edition.normalization_version,
        scales=scales,
    ).model_dump(mode="json")
    (destination / "anchor-panels.json").write_text(
        json.dumps(panel_set, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "score-scales.json").write_text(
        json.dumps(scale_set, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"panels": panel_set, "scales": scale_set}
