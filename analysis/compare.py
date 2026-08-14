from __future__ import annotations

import hashlib
import json

from scipy.stats import rankdata

from umi.capability import score_capability
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.readiness import scoring_dataset
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
    available = {
        model_id: {
            (item.benchmark_id, item.cohort_key)
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
                if item.model_id in requested and (item.benchmark_id, item.cohort_key) in common
            ),
            "efficiency": (),
            "task_economics": (),
        }
    )
    computation = score_capability(filtered, config)
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
    return {
        "comparison_group_id": group_id,
        "comparison_model_ids": requested,
        "common_evidence_profile_id": profile_id,
        "common_benchmark_series": [
            {"benchmark_id": benchmark_id, "cohort_key": cohort_key}
            for benchmark_id, cohort_key in sorted(common)
        ],
        "component": "capability",
        "scores": [
            {
                "model_id": model_id,
                "score": components[model_id].score,
                "coverage": components[model_id].coverage,
                "provisional": components[model_id].provisional,
                "rank": float(rank),
            }
            for model_id, rank in zip(requested, ranks, strict=True)
        ],
        "normalization_method": "configured per benchmark series",
        "publication_label": "real evidence, provisional common-evidence comparison",
    }
