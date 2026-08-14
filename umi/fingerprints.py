from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from pydantic import BaseModel

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import Provenance
from umi.version import ENGINE_VERSION, FORMULA_VERSION, NORMALIZATION_VERSION


def _ordered(items: Iterable[BaseModel], key: str) -> list[dict[str, object]]:
    return [
        item.model_dump(mode="json")
        for item in sorted(items, key=lambda value: str(getattr(value, key)))
    ]


def canonical_dataset_payload(dataset: Dataset, config: ProjectConfig) -> dict[str, object]:
    records: tuple[Provenance, ...] = (
        *dataset.benchmarks,
        *dataset.pricing,
        *dataset.efficiency,
        *dataset.task_economics,
        *dataset.external_indexes,
    )
    return {
        "models": _ordered(dataset.models, "id"),
        "records": _ordered(records, "record_id"),
        "config_fingerprint": config.fingerprint,
        "engine_version": ENGINE_VERSION,
        "formula_version": FORMULA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
    }


def dataset_fingerprint(dataset: Dataset, config: ProjectConfig) -> str:
    payload = canonical_dataset_payload(dataset, config)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()
