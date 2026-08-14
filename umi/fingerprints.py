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


def _digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def complete_audit_payload(dataset: Dataset, config: ProjectConfig) -> dict[str, object]:
    records: tuple[Provenance, ...] = (
        *dataset.benchmarks,
        *dataset.pricing,
        *dataset.efficiency,
        *dataset.task_economics,
        *dataset.external_indexes,
        *dataset.release_claims,
    )
    return {
        "models": _ordered(dataset.models, "id"),
        "records": _ordered(records, "record_id"),
        "config_fingerprint": config.fingerprint,
        "engine_version": ENGINE_VERSION,
        "formula_version": FORMULA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "scored_audit_fingerprint": dataset.scored_audit_fingerprint,
        "complete_audit_fingerprint": dataset.complete_audit_fingerprint,
        "adapter_versions": sorted(dataset.adapter_versions),
    }


def scoring_context_payload(dataset: Dataset, config: ProjectConfig) -> dict[str, object]:
    """Canonical identity of the exact, readiness-filtered scoring context.

    Call this only with the dataset returned by ``scoring_dataset``. Complete-audit-only records,
    pricing, external references, and complete-audit metadata are intentionally absent.
    """
    records: tuple[Provenance, ...] = (
        *dataset.benchmarks,
        *dataset.efficiency,
        *dataset.task_economics,
    )
    return {
        "models": [
            item.model_dump(mode="json", exclude={"source_snapshot_ids", "notes"})
            for item in sorted(dataset.models, key=lambda model: model.id)
        ],
        "scored_records": _ordered(records, "record_id"),
        "scoring_config_fingerprint": config.fingerprint,
        "engine_version": ENGINE_VERSION,
        "formula_version": FORMULA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "scored_audit_fingerprint": dataset.scored_audit_fingerprint,
        "adapter_versions": sorted(dataset.adapter_versions),
    }


def dataset_fingerprint(dataset: Dataset, config: ProjectConfig) -> str:
    """Complete audit fingerprint, including diagnostic and rejected-context metadata."""
    return _digest(complete_audit_payload(dataset, config))


def scored_data_fingerprint(dataset: Dataset, config: ProjectConfig) -> str:
    """Fingerprint only the exact data and governed configuration that scoring consumes."""
    return _digest(scoring_context_payload(dataset, config))
