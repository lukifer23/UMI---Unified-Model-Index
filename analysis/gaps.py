from __future__ import annotations

from collections import Counter

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.readiness import is_scoring_ready


def pilot_gap_report(dataset: Dataset, config: ProjectConfig) -> dict[str, object]:
    """Return an exact evidence/gate matrix for the configured pilot cohort."""
    models = {item.id: item for item in dataset.models}
    cells: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for definition in config.benchmarks:
        for model_id, model in sorted(models.items()):
            measurements = [
                item
                for item in dataset.benchmarks
                if item.model_id == model_id and item.benchmark_id == definition.id
            ]
            ready = [item for item in measurements if is_scoring_ready(item, model)]
            references = [
                item
                for item in dataset.external_indexes
                if item.model_id == model_id and item.index_id == definition.id
            ]
            claims = [
                item
                for item in dataset.release_claims
                if item.model_id == model_id and item.benchmark_id == definition.id
            ]
            if ready:
                status = "ready_scored"
                ids = [item.record_id for item in ready]
            elif measurements:
                status = "diagnostic_measurement"
                ids = [item.record_id for item in measurements]
            elif references:
                status = "diagnostic_reference"
                ids = [item.record_id for item in references]
            elif claims:
                status = "vendor_claim_only"
                ids = [item.record_id for item in claims]
            else:
                status = "missing"
                ids = []
            counts[status] += 1
            cells.append(
                {
                    "benchmark_id": definition.id,
                    "domain": definition.domain.value,
                    "family": definition.family,
                    "model_id": model_id,
                    "record_ids": ids,
                    "status": status,
                }
            )

    workload_rows: list[dict[str, object]] = []
    for category, weight in config.weights.workload_weights.items():
        for model_id, model in sorted(models.items()):
            efficiency = [
                item
                for item in dataset.efficiency
                if item.model_id == model_id and item.workload_category == category
            ]
            economics = [
                item
                for item in dataset.task_economics
                if item.model_id == model_id and item.workload_category == category
            ]
            workload_rows.append(
                {
                    "model_id": model_id,
                    "workload_category": category.value,
                    "configured_weight": weight,
                    "efficiency_ready_record_ids": [
                        item.record_id for item in efficiency if is_scoring_ready(item, model)
                    ],
                    "efficiency_diagnostic_record_ids": [
                        item.record_id for item in efficiency if not is_scoring_ready(item, model)
                    ],
                    "economics_ready_record_ids": [
                        item.record_id for item in economics if is_scoring_ready(item, model)
                    ],
                }
            )

    pricing = {
        model_id: [item.record_id for item in dataset.pricing if item.model_id == model_id]
        for model_id in sorted(models)
    }
    ineligible_models = [
        model.id
        for model in models.values()
        if not config.eligibility.release_start
        <= model.release_date
        <= config.eligibility.release_end
    ]
    blockers = [
        (
            "Capability lacks ready evidence in at least "
            f"{config.eligibility.minimum_capability_domains} configured domains for every model."
        ),
        "No workload category has ready all-model Efficiency evidence.",
        "No workload category has ready all-model successful-task Economics evidence.",
        (
            "Token tariffs cannot be converted to task cost without compatible per-attempt "
            "resource usage."
        ),
    ]
    if ineligible_models:
        blockers.append(
            "Release-window-ineligible configurations: " + ", ".join(sorted(ineligible_models))
        )
    return {
        "label": "real evidence gap audit; not a ranking",
        "pilot_model_ids": sorted(models),
        "capability_cells": cells,
        "capability_cell_counts": dict(sorted(counts.items())),
        "workload_rows": workload_rows,
        "pricing_record_ids": pricing,
        "headline_blockers": blockers,
    }
