from __future__ import annotations

import re
from pathlib import Path

import yaml

from umi.schemas import CrosswalkStatus, ModelCrosswalk, ModelCrosswalkEntry


def load_yaml(path: str | Path) -> dict[str, object]:
    with Path(path).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def exact_entry(
    crosswalk: ModelCrosswalk, source_id: str, artifact_id: str, source_model_id: str
) -> ModelCrosswalkEntry | None:
    matches = [
        item
        for item in crosswalk.entries
        if item.source_id == source_id
        and item.source_artifact_id == artifact_id
        and item.source_model_id == source_model_id
        and item.status == CrosswalkStatus.EXACT
    ]
    if len(matches) > 1:
        raise ValueError(f"duplicate exact crosswalk for {source_id}/{source_model_id}")
    return matches[0] if matches else None


def identifier(value: str) -> str:
    rendered = re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-._")
    if not rendered:
        raise ValueError("cannot derive an identifier from an empty value")
    return rendered
