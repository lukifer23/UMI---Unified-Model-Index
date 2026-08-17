"""Governed Public scoring bundle. Revalidated zip-bound evidence, not a second scorer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from umi.edition import (
    GOVERNED_PUBLIC_INDEX,
    ConfigModel,
    PublicEditionConfig,
    load_public_edition_config,
)
from umi.identity import PublicSystemIdentity, load_public_identities
from umi.public import (
    ROOT,
    SeriesPoint,
    SeriesSpec,
    entity_map_from_identities,
    epoch_points,
    public_series_specs,
)
from umi.public_certificate import (
    EPOCH_ATTRIBUTION,
    EPOCH_LICENSE,
    EPOCH_SHA256,
    EPOCH_SNAPSHOT_ID,
    verify_epoch_zip,
)
from umi.public_evidence import PublicEvidenceRecord, PublicSeriesContract


class PublicScoringBundle(ConfigModel):
    edition_id: str
    release_class: str
    formula_version: str
    source_artifact_id: str
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_license: str
    source_attribution: str
    entity_ids: tuple[str, ...]
    series: tuple[PublicSeriesContract, ...]
    evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def reject_incomplete_or_unbound_evidence(self) -> PublicScoringBundle:
        if self.source_artifact_sha256 != EPOCH_SHA256:
            raise ValueError("public bundle zip checksum does not match the registry")
        series_ids = [item.series_id for item in self.series]
        if len(series_ids) != len(set(series_ids)):
            raise ValueError("public bundle series IDs must be unique")
        required_entities = set(self.entity_ids)
        for contract in self.series:
            if set(contract.accepted_entity_ids) != required_entities:
                raise ValueError(f"{contract.series_id} is missing a required entity")
        return self


def _digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def _series_contract(
    spec: SeriesSpec,
    points: tuple[SeriesPoint, ...],
    digest: str,
) -> PublicSeriesContract:
    records = tuple(
        PublicEvidenceRecord(
            series_id=spec["id"],
            config_id=item.config_id,
            entity_id=item.entity_id,
            raw=item.raw,
            complete=item.complete,
            source_name=item.source_name,
            member=spec["member"],
            field=spec["field"],
            source_artifact_id=EPOCH_SNAPSHOT_ID,
            source_artifact_sha256=digest,
        )
        for item in points
    )
    accepted = tuple(item.entity_id for item in records if item.entity_id is not None)
    return PublicSeriesContract(
        series_id=spec["id"],
        member=spec["member"],
        field=spec["field"],
        kind=spec["kind"],
        component=spec["component"],
        harness=spec.get("harness"),
        panel_filter=spec.get("panel_filter"),
        anchor_n=len(records),
        accepted_entity_ids=accepted,
        records=records,
    )


def load_public_scoring_bundle(
    *,
    edition_name: str = "v0.5",
    config: PublicEditionConfig | None = None,
    identities: tuple[PublicSystemIdentity, ...] | None = None,
) -> PublicScoringBundle:
    edition = config or load_public_edition_config(edition=edition_name)
    loaded = identities or load_public_identities(edition=edition_name)
    digest = verify_epoch_zip()
    mapping = entity_map_from_identities(loaded, edition=edition_name)
    required = {item.entity_id for item in loaded}
    contracts: list[PublicSeriesContract] = []
    blockers: list[dict[str, Any]] = []
    suffixes = edition.normalization.high_effort_suffixes
    for spec in public_series_specs(edition):
        points = epoch_points(
            spec["member"],
            spec["field"],
            require_harness=spec.get("harness"),
            identities=loaded,
            panel_filter=spec.get("panel_filter"),
            entity_map=mapping,
            high_effort_suffixes=suffixes,
        )
        contract = _series_contract(spec, points, digest)
        pilots = set(contract.accepted_entity_ids)
        if pilots != required or contract.anchor_n < edition.eligibility.minimum_anchor_panel:
            blockers.append(
                {
                    "series": spec["id"],
                    "pilots": sorted(pilots),
                    "anchor_n": contract.anchor_n,
                    "reason": "series missing a pilot or an 8+ anchor panel",
                }
            )
            continue
        contracts.append(contract)
    if blockers:
        raise ValueError("required public series failed: " + str(blockers))
    unsigned = {
        "edition_id": edition.edition_id,
        "release_class": edition.release_class,
        "source_artifact_sha256": digest,
        "entity_ids": [item.entity_id for item in loaded],
        "series": [
            {
                "series_id": item.series_id,
                "records": [
                    {
                        "config_id": row.config_id,
                        "entity_id": row.entity_id,
                        "raw": row.raw,
                    }
                    for row in sorted(item.records, key=lambda row: row.config_id)
                ],
            }
            for item in contracts
        ],
    }
    bundle = {
        "edition_id": edition.edition_id,
        "release_class": edition.release_class,
        "formula_version": edition.formula_version,
        "source_artifact_id": EPOCH_SNAPSHOT_ID,
        "source_artifact_sha256": digest,
        "source_license": EPOCH_LICENSE,
        "source_attribution": EPOCH_ATTRIBUTION,
        "entity_ids": tuple(item.entity_id for item in loaded),
        "series": contracts,
        "evidence_fingerprint": _digest(unsigned),
    }
    return PublicScoringBundle.model_validate(bundle)


def bundle_points(bundle: PublicScoringBundle, series_id: str) -> tuple[SeriesPoint, ...]:
    contract = next(item for item in bundle.series if item.series_id == series_id)
    return tuple(
        SeriesPoint(
            config_id=item.config_id,
            entity_id=item.entity_id,
            raw=item.raw,
            complete=item.complete,
            source_name=item.source_name,
        )
        for item in contract.records
    )


def write_public_scoring_bundle(
    bundle: PublicScoringBundle,
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    if bundle.release_class != GOVERNED_PUBLIC_INDEX:
        raise ValueError("public scoring-bundle artifact is a governed-index surface")
    destination = output_dir or ROOT / "data" / "editions" / edition_name / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    payload = bundle.model_dump(mode="json")
    (destination / "public-scoring-bundle.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload
