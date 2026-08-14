from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import ScoringResult

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "dataset.schema.json": Dataset,
    "config.schema.json": ProjectConfig,
    "scoring-result.schema.json": ScoringResult,
}


def rendered_schemas() -> dict[str, str]:
    return {
        name: json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        for name, model in SCHEMA_MODELS.items()
    }


def generate_schemas(output_dir: str | Path) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    for name, rendered in rendered_schemas().items():
        (root / name).write_text(rendered, encoding="utf-8")

