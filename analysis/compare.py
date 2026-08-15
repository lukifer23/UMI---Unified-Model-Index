from __future__ import annotations

import hashlib
import json

from scipy.stats import rankdata

from umi.capability import score_capability
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.readiness import scoring_dataset
from umi.schemas import BenchmarkDefinition
from umi.validation import validate_dataset


def common_capability_comparison(
    dataset: Dataset, config: ProjectConfig, model_ids: tuple[str, ...]
) -> dict[str, object]:
    """Calculate Capability only from ready benchmark series common to every requested model."""
    if len(model_ids) < 2 or len(set(model_ids)) != len(model_ids):
        raise ValueError("compare requires at least two distinct model IDs")
    validate_dataset(dataset, config).raise_for_errors()
    scored, _ = scoring_dataset(dataset)
    requested = tuple(sorted(model_ids))
    known = {model.id for model in scored.models}
    missing = sorted(set(requested) - known)
    if missing:
        raise ValueError("unknown comparison model IDs: " + ", ".join(missing))
    canonical: dict[str, tuple[str, str]] = {}
    grouped: dict[tuple[str, str], list[BenchmarkDefinition]] = {}
    for definition in config.benchmarks:
        key = (definition.family, definition.representation_group or definition.id)
        grouped.setdefault(key, []).append(definition)
    for (_, group_id), members in grouped.items():
        canonical_definition = next(
            item for item in members if item.selection_priority == 0
        )
        for member in members:
            canonical[member.id] = (canonical_definition.id, group_id)
    available = {
        model_id: {
            (*canonical[item.benchmark_id], item.cohort_key)
            for item in scored.benchmarks
            if item.model_id == model_id
        }
        for model_id in requested
    }
    common = set.intersection(*available.values())
    filtered = scored.model_copy(
        update={
            "models": tuple(item for item in scored.models if item.id in requested),
            "benchmarks": tuple(
                item
                for item in scored.benchmarks
                if item.model_id in requested
                and (*canonical[item.benchmark_id], item.cohort_key) in common
            ),
            "efficiency": (),
            "task_economics": (),
        }
    )
    computation = score_capability(filtered, config, normalization_dataset=scored)
    components = computation.components
    profile_ids = {
        item.evidence_profile.id for item in components.values() if item.evidence_profile
    }
    profile_id = next(iter(profile_ids)) if len(profile_ids) == 1 else None
    values = [components[item].score for item in requested]
    numeric_values = [value for value in values if value is not None]
    ranks = (
        rankdata([-value for value in numeric_values], method="average")
        if len(numeric_values) == len(values)
        else []
    )
    group_id = hashlib.sha256(
        json.dumps(
            {"models": requested, "series": sorted(common), "config": config.fingerprint},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    contribution_rows = {
        model_id: [item.model_dump(mode="json") for item in computation.contributions[model_id]]
        for model_id in requested
    }
    return {
        "comparison_group_id": group_id,
        "comparison_model_ids": requested,
        "common_evidence_profile_id": profile_id,
        "common_benchmark_series": [
            {
                "benchmark_id": benchmark_id,
                "canonical_representation_group": representation_group,
                "cohort_key": cohort_key,
            }
            for benchmark_id, representation_group, cohort_key in sorted(common)
        ],
        "component": "capability",
        "scores": [
            {
                "model_id": model_id,
                "score": components[model_id].score,
                "normalized_composite_score": components[model_id].score,
                "coverage": components[model_id].coverage,
                "provisional": components[model_id].provisional,
                "rank": float(rank),
                "evidence_profile_id": components[model_id].evidence_profile_id,
                "normalization_panel_ids": components[model_id].normalization_panel_ids,
                "score_scale_id": components[model_id].score_scale_id,
                "score_semantics": components[model_id].score_semantics,
                "primary_raw_results": [
                    {
                        "benchmark_id": item["benchmark_id"],
                        "cohort_key": item["cohort_key"],
                        "raw_value": item["raw_value"],
                        "raw_unit": item["raw_unit"],
                        "direction": item["direction"],
                        "source_uncertainty": item["source_uncertainty"],
                    }
                    for item in contribution_rows[model_id]
                ],
                "contributions": contribution_rows[model_id],
            }
            for model_id, rank in zip(requested, ranks, strict=True)
        ],
        "normalization_panels": tuple(
            computation.normalization_panels[panel_id].model_dump(mode="json")
            for panel_id in sorted(
                {
                    panel_id
                    for model_id in requested
                    for panel_id in components[model_id].normalization_panel_ids
                }
            )
        ),
        "score_scale": computation.score_scales[requested[0]].model_dump(mode="json"),
        "primary_result_semantics": "raw benchmark metrics",
        "normalization_method": "bundle-wide stable panel per canonical benchmark series",
        "publication_label": "real evidence, provisional common-evidence comparison",
    }
