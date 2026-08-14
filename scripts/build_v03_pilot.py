from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from umi.adapters import (
    adapt_aa_facts,
    adapt_arena_json,
    adapt_deepswe_facts,
    adapt_epoch_csv,
    assemble_pilot_dataset,
)
from umi.loading import load_model_crosswalk, load_source_registry
from umi.schemas import ModelConfiguration, ScoringDisposition

ROOT = Path(__file__).parents[1]
SOURCE_ROOT = ROOT / "data" / "sources" / "v0.3"
PILOT_ROOT = ROOT / "data" / "pilots" / "v0.3"
RAW_ROOT = PILOT_ROOT / "raw"
PROCESSED_ROOT = PILOT_ROOT / "processed"


def _hash(value: object) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def _write_yaml(path: Path, key: str, values: tuple[Any, ...]) -> None:
    payload = {key: [item.model_dump(mode="json", exclude_none=True) for item in values]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def main() -> None:
    models_raw = yaml.safe_load((RAW_ROOT / "models.yaml").read_text(encoding="utf-8"))
    models = TypeAdapter(tuple[ModelConfiguration, ...]).validate_python(models_raw["models"])
    crosswalk = load_model_crosswalk(SOURCE_ROOT / "crosswalk.yaml")
    registry = load_source_registry(ROOT / "data" / "sources" / "registry.yaml")
    results = (
        adapt_aa_facts(SOURCE_ROOT / "aa-reviewed-facts-2026-08-14.yaml", crosswalk),
        adapt_epoch_csv(
            SOURCE_ROOT / "epoch-eci-benchmarks-2026-08-14.csv",
            crosswalk,
            source_id="epoch-eci",
            artifact_id="epoch-eci-matrix-2026-08-14",
        ),
        adapt_arena_json(
            SOURCE_ROOT / "arena-agent-2026-08-14.json",
            crosswalk,
            source_id="arena-agent",
            artifact_id="arena-agent-2026-08-14",
            upstream_revision="08dd89df7a8aa9df2ead3799f6422af4ad2e97a7",
            subset="agent",
        ),
        adapt_arena_json(
            SOURCE_ROOT / "arena-text-style-control-2026-08-14.json",
            crosswalk,
            source_id="arena-text",
            artifact_id="arena-text-2026-08-14",
            upstream_revision="08dd89df7a8aa9df2ead3799f6422af4ad2e97a7",
            subset="text_style_control",
        ),
        adapt_deepswe_facts(
            SOURCE_ROOT / "deepswe-reviewed-facts-2026-08-13.yaml", crosswalk
        ),
    )
    dataset = assemble_pilot_dataset(models, results)
    relevant_ids = {entry.source_artifact_id for entry in crosswalk.entries}
    snapshots = [
        item.model_dump(mode="json")
        for item in registry.snapshots
        if item.id in relevant_ids
    ]
    complete_payload = {
        "snapshots": snapshots,
        "crosswalk": crosswalk.model_dump(mode="json"),
        "adapter_results": [item.model_dump(mode="json") for item in results],
    }
    scored_records = [
        item.model_dump(mode="json")
        for item in (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
        if item.scoring_disposition == ScoringDisposition.SCORED
    ]
    scored_artifacts = {item["source_artifact_id"] for item in scored_records}
    scored_payload = {
        "snapshots": [item for item in snapshots if item["id"] in scored_artifacts],
        "exact_crosswalk": [
            item.model_dump(mode="json")
            for item in crosswalk.entries
            if item.source_artifact_id in scored_artifacts and item.status.value == "exact"
        ],
        "accepted_scoring_records": scored_records,
    }
    adapter_versions = tuple(sorted({item.adapter_id for item in results}))
    dataset = dataset.model_copy(
        update={
            "scored_audit_fingerprint": _hash(scored_payload),
            "complete_audit_fingerprint": _hash(complete_payload),
            "adapter_versions": adapter_versions,
        }
    )
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    _write_yaml(RAW_ROOT / "benchmarks.yaml", "measurements", dataset.benchmarks)
    _write_yaml(RAW_ROOT / "pricing.yaml", "pricing", dataset.pricing)
    _write_yaml(RAW_ROOT / "task_efficiency.yaml", "measurements", dataset.efficiency)
    _write_yaml(RAW_ROOT / "task_economics.yaml", "measurements", dataset.task_economics)
    _write_yaml(RAW_ROOT / "external_indexes.yaml", "measurements", dataset.external_indexes)
    (RAW_ROOT / "audit.yaml").write_text(
        yaml.safe_dump(
            {
                "scored_audit_fingerprint": dataset.scored_audit_fingerprint,
                "complete_audit_fingerprint": dataset.complete_audit_fingerprint,
                "adapter_versions": list(adapter_versions),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report = {
        "label": "real evidence, provisional partial ranking",
        "sources": [item.model_dump(mode="json") for item in results],
        "scored_audit_fingerprint": dataset.scored_audit_fingerprint,
        "complete_audit_fingerprint": dataset.complete_audit_fingerprint,
    }
    (PROCESSED_ROOT / "adaptation-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
