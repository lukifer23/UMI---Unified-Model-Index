from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from umi.adapters.models import AdaptationResult
from umi.config import ProjectConfig
from umi.loading import Dataset, SourceRegistry
from umi.schemas import (
    AcceptanceManifest,
    BenchmarkContribution,
    ModelCrosswalk,
    NormalizationPanel,
    OverlapPolicy,
    ScoreScale,
    ScoringResult,
)

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "dataset.schema.json": Dataset,
    "config.schema.json": ProjectConfig,
    "scoring-result.schema.json": ScoringResult,
    "source-registry.schema.json": SourceRegistry,
    "model-crosswalk.schema.json": ModelCrosswalk,
    "overlap-policy.schema.json": OverlapPolicy,
    "adaptation-result.schema.json": AdaptationResult,
    "acceptance-manifest.schema.json": AcceptanceManifest,
    "normalization-panel.schema.json": NormalizationPanel,
    "score-scale.schema.json": ScoreScale,
    "benchmark-contribution.schema.json": BenchmarkContribution,
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
