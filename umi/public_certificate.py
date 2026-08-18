"""Governed Public index certificate. Presentation of published scores, not a second scorer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import Field

from umi.edition import ConfigModel
from umi.public_paths import resolve_epoch_zip

CERTIFICATE_VERSION = "umi-public-certificate-v0.5"
EPOCH_SNAPSHOT_ID = "epoch-benchmark-data-2026-08-14"
EPOCH_SHA256 = "35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b"
EPOCH_LICENSE = "CC-BY-4.0"
EPOCH_ATTRIBUTION = "Epoch AI, AI Benchmarking Hub, 2026"


class PublicIndexModelRow(ConfigModel):
    entity_id: str
    named_release: str
    entity_kind: str
    effort_setting: str
    umi_public: float
    rank: int
    interval_low: float | None = None
    interval_high: float | None = None
    rank_low: int | None = None
    rank_high: int | None = None
    interval_status: str
    indistinguishable_from: tuple[str, ...] = ()


class PublicIndexCertificate(ConfigModel):
    certificate_version: str
    status: str
    edition_id: str
    formula_version: str
    scored_data_fingerprint: str
    validation_valid: bool
    source_artifact_id: str
    source_artifact_sha256: str
    source_license: str
    source_attribution: str
    series: tuple[str, ...]
    models: tuple[PublicIndexModelRow, ...]
    pairwise_indistinguishable: tuple[tuple[str, str], ...]
    limitations: tuple[str, ...]
    result_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


def _digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def verify_epoch_zip(zip_path: Path | str | None = None) -> str:
    archive = Path(zip_path) if zip_path is not None else resolve_epoch_zip()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != EPOCH_SHA256:
        raise ValueError(
            f"Epoch zip checksum {digest} does not match registry {EPOCH_SHA256}"
        )
    return digest


def overlapping_pairs(models: list[dict[str, Any]]) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for index, left in enumerate(models):
        low_left = left.get("interval_low")
        high_left = left.get("interval_high")
        if low_left is None or high_left is None:
            continue
        for right in models[index + 1 :]:
            low_right = right.get("interval_low")
            high_right = right.get("interval_high")
            if low_right is None or high_right is None:
                continue
            if high_left < low_right or high_right < low_left:
                continue
            pair = tuple(sorted((left["entity_id"], right["entity_id"])))
            pairs.append((pair[0], pair[1]))
    return tuple(pairs)


def build_public_certificate(
    payload: dict[str, Any],
    validation: dict[str, Any],
    uncertainty: dict[str, Any],
) -> dict[str, Any]:
    if not validation.get("valid"):
        raise ValueError("public certificate requires a valid audit")
    zip_digest = verify_epoch_zip()
    by_id = {item["entity_id"]: item for item in uncertainty["models"]}
    rows = []
    for item in sorted(payload["models"], key=lambda row: row["rank"]):
        interval = by_id[item["entity_id"]]
        rows.append(
            {
                "entity_id": item["entity_id"],
                "named_release": item["named_release"],
                "entity_kind": item["entity_kind"],
                "effort_setting": item["effort_setting"],
                "umi_public": item["umi_public"],
                "rank": item["rank"],
                "interval_low": interval["interval_low"],
                "interval_high": interval["interval_high"],
                "rank_low": interval["rank_low"],
                "rank_high": interval["rank_high"],
                "interval_status": interval["interval_status"],
            }
        )
    pairs = overlapping_pairs(rows)
    neighbors: dict[str, list[str]] = {row["entity_id"]: [] for row in rows}
    for left, right in pairs:
        neighbors[left].append(right)
        neighbors[right].append(left)
    for row in rows:
        row["indistinguishable_from"] = tuple(sorted(neighbors[row["entity_id"]]))
    unsigned = {
        "certificate_version": CERTIFICATE_VERSION,
        "status": "provisional_public_score",
        "edition_id": payload["edition_id"],
        "formula_version": payload["formula_version"],
        "scored_data_fingerprint": payload["scored_data_fingerprint"],
        "validation_valid": True,
        "source_artifact_id": EPOCH_SNAPSHOT_ID,
        "source_artifact_sha256": zip_digest,
        "source_license": EPOCH_LICENSE,
        "source_attribution": EPOCH_ATTRIBUTION,
        "series": tuple(payload["series"]),
        "models": rows,
        "pairwise_indistinguishable": pairs,
        "limitations": tuple(uncertainty["limitations"]),
    }
    certificate = {**unsigned, "result_fingerprint": _digest(unsigned)}
    return PublicIndexCertificate.model_validate(certificate).model_dump(mode="json")
