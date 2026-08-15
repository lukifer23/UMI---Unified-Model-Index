from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from umi.derived_metrics import derive_efficiency_metric
from umi.loading import Dataset
from umi.schemas import ScoringDisposition


def _display_name(model_id: str, model_names: dict[str, str]) -> str:
    return model_names.get(model_id, model_id)


def _source(
    source_id: str,
    label: str,
    path: str,
) -> dict[str, Any]:
    return {
        "id": source_id,
        "label": label,
        "path": path,
    }


def build_pilot_dashboard(
    dataset: Dataset,
    estimates: Iterable[dict[str, Any]],
    gap_report: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic presentation contract for the real v0.3 pilot."""
    estimates = list(estimates)
    model_names = {
        model.id: f"{model.named_release} ({model.configuration})"
        for model in dataset.models
        if model.named_release is not None
    }
    model_short_names = {
        "claude-opus-5-max": "Opus 5",
        "claude-fable-5-max": "Fable 5",
        "gpt-5.6-sol-max": "GPT-5.6 Sol",
        "kimi-k3-max": "Kimi K3",
        "glm-5.2-max": "GLM-5.2",
    }
    benchmark_short_names = {
        "hle": "HLE",
        "arc-agi-2": "ARC-2",
        "critpt": "CritPt",
        "deepswe-v1.1": "DeepSWE",
        "gpqa-diamond": "GPQA",
        "scicode": "SciCode",
    }
    ordered_models = [model.id for model in dataset.models]
    estimates_by_model = {item["model_id"]: item for item in estimates}

    summary_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    for model_id in ordered_models:
        item = estimates_by_model[model_id]
        label = _display_name(model_id, model_names)
        profile_id = item["capability"]["evidence_profile"]["id"]
        summary_rows.append(
            {
                "model": label,
                "model_id": model_id,
                "model_short": model_short_names[model_id],
                "capability": item["capability"]["score"],
                "capability_coverage": item["capability"]["coverage"],
                "capability_domains": len(item["capability_domains"]),
                "efficiency": item["efficiency"]["score"],
                "efficiency_coverage": item["efficiency"]["coverage"],
                "economics": item["economics"]["score"],
                "economics_coverage": item["economics"]["coverage"],
                "partial_overall": item["partial_overall_estimate"],
                "headline": "Not eligible" if item["headline_overall"] is None else "Eligible",
                "confidence": item["confidence"].title(),
                "capability_profile": profile_id[:12],
                "comparability": item["capability"]["comparability_status"],
            }
        )
        for component in ("capability", "efficiency"):
            score = item[component]["score"]
            if score is not None:
                component_rows.append(
                    {
                        "model": label,
                        "model_id": model_id,
                        "model_short": model_short_names[model_id],
                        "component": {"capability": "Cap.", "efficiency": "Eff."}[component],
                        "score": score,
                    }
                )
        for component in ("capability", "efficiency", "economics"):
            coverage_rows.append(
                {
                    "model": label,
                    "model_id": model_id,
                    "model_short": model_short_names[model_id],
                    "component": {
                        "capability": "Cap.",
                        "efficiency": "Eff.",
                        "economics": "Econ.",
                    }[component],
                    "coverage": item[component]["coverage"],
                }
            )

    benchmark_rows = [
        {
            "model": _display_name(record.model_id, model_names),
            "model_id": record.model_id,
            "model_short": model_short_names[record.model_id],
            "benchmark": record.benchmark_id,
            "benchmark_short": benchmark_short_names.get(record.benchmark_id, record.benchmark_id),
            "score": record.value,
            "cohort": record.cohort_key,
            "record_id": record.record_id,
            "source": record.source.organization,
        }
        for record in dataset.benchmarks
        if record.scoring_disposition == ScoringDisposition.SCORED
    ]
    resource_rows = []
    for record in dataset.efficiency:
        if record.scoring_disposition != ScoringDisposition.SCORED:
            continue
        resource_rows.append(
            {
                "model": _display_name(record.model_id, model_names),
                "model_id": record.model_id,
                "model_short": model_short_names[record.model_id],
                "success_rate": record.success_rate,
                "attempts": record.attempts,
                "effective_input_tokens": derive_efficiency_metric(
                    record, "effective_input_tokens"
                ),
                "effective_output_tokens": derive_efficiency_metric(
                    record, "effective_output_tokens"
                ),
                "effective_agent_steps": derive_efficiency_metric(record, "effective_agent_steps"),
                "record_id": record.record_id,
            }
        )

    gap_rows = [
        {
            "status": {
                "ready_scored": "Ready",
                "diagnostic_measurement": "Diagnostic",
                "diagnostic_reference": "Reference",
                "vendor_claim_only": "Vendor claim",
                "missing": "Missing",
            }[status],
            "cells": count,
        }
        for status, count in gap_report["capability_cell_counts"].items()
    ]
    scored_cells = gap_report["capability_cell_counts"]["ready_scored"]
    total_cells = sum(gap_report["capability_cell_counts"].values())
    overview = [
        {
            "pilot_models": len(dataset.models),
            "headline_ready": sum(item["headline_overall"] is not None for item in estimates),
            "scored_capability_cells": scored_cells,
            "total_capability_cells": total_cells,
            "max_capability_coverage": max(item["capability"]["coverage"] for item in estimates),
            "efficiency_coverage": max(item["efficiency"]["coverage"] for item in estimates),
            "economics_coverage": max(item["economics"]["coverage"] for item in estimates),
        }
    ]

    estimate_source = _source(
        "pilot_estimates",
        "Governed UMI partial estimates",
        "data/pilots/v0.3/processed/model-specific-partial-estimates.json",
    )
    benchmark_source = _source(
        "accepted_benchmarks",
        "Accepted benchmark records",
        "data/pilots/v0.3/raw/benchmarks.yaml",
    )
    efficiency_source = _source(
        "accepted_efficiency",
        "Accepted DeepSWE harness resources",
        "data/pilots/v0.3/raw/task_efficiency.yaml",
    )
    gap_source = _source(
        "pilot_gaps",
        "Configured capability gap matrix",
        "data/pilots/v0.3/processed/pilot-gap-report.json",
    )
    sources = [estimate_source, benchmark_source, efficiency_source, gap_source]

    return {
        "surface": "dashboard",
        "manifest": {
            "version": 1,
            "surface": "dashboard",
            "title": "UMI v0.3.5 — five-model pilot evidence report",
            "description": (
                "A reproducible view of current accepted evidence, partial component estimates, "
                "coverage, and the gates that prevent a headline UMI ranking."
            ),
            "generatedAt": "2026-08-14T00:00:00Z",
            "filters": [
                {
                    "id": "model",
                    "label": "Model configuration",
                    "dataset": "model_summary",
                    "field": "model",
                    "includeAll": True,
                    "targets": [
                        {"dataset": "component_scores", "field": "model"},
                        {"dataset": "coverage", "field": "model"},
                        {"dataset": "benchmarks", "field": "model"},
                        {"dataset": "resources", "field": "model"},
                    ],
                }
            ],
            "cards": [
                {
                    "id": "pilot_scope",
                    "description": "Exact named-release and effort configurations in the pilot.",
                    "dataset": "overview",
                    "sourceId": "pilot_estimates",
                    "metrics": [{"label": "Pilot configurations", "field": "pilot_models"}],
                },
                {
                    "id": "headline_state",
                    "description": "Models clearing every configured headline gate.",
                    "dataset": "overview",
                    "sourceId": "pilot_estimates",
                    "metrics": [{"label": "Headline-ready", "field": "headline_ready"}],
                },
                {
                    "id": "capability_cells",
                    "description": "Ready scored cells across the complete capability matrix.",
                    "dataset": "overview",
                    "sourceId": "pilot_gaps",
                    "metrics": [
                        {"label": "Ready cells", "field": "scored_capability_cells"},
                        {"label": "Configured cells", "field": "total_capability_cells"},
                    ],
                },
                {
                    "id": "coverage_ceiling",
                    "description": "Best current model coverage by component.",
                    "dataset": "overview",
                    "sourceId": "pilot_estimates",
                    "metrics": [
                        {
                            "label": "Max capability coverage",
                            "field": "max_capability_coverage",
                            "format": "percent",
                        },
                        {
                            "label": "Efficiency coverage",
                            "field": "efficiency_coverage",
                            "format": "percent",
                        },
                        {
                            "label": "Economics coverage",
                            "field": "economics_coverage",
                            "format": "percent",
                        },
                    ],
                },
            ],
            "charts": [
                {
                    "id": "component_scores",
                    "title": "Partial component positions",
                    "subtitle": (
                        "Diagnostic normalized scores; compare only models with matching "
                        "evidence support."
                    ),
                    "headerMarkdown": (
                        "These are **not headline UMI scores**. A value of 0 can be the "
                        "cohort minimum, "
                        "not zero task performance."
                    ),
                    "type": "bar",
                    "dataset": "component_scores",
                    "sourceId": "pilot_estimates",
                    "encodings": {
                        "x": {
                            "field": "model_short",
                            "type": "nominal",
                            "label": "Model",
                        },
                        "y": {
                            "field": "score",
                            "type": "quantitative",
                            "label": "Normalized score",
                        },
                        "color": {"field": "component", "type": "nominal", "label": "Component"},
                    },
                    "yAxisTitle": "Normalized score (0–100)",
                    "valueFormat": "number",
                    "layout": "full",
                },
                {
                    "id": "component_coverage",
                    "title": "Coverage remains the binding constraint",
                    "subtitle": (
                        "Absolute configured coverage, not the share of evidence available "
                        "for one model."
                    ),
                    "type": "bar",
                    "dataset": "coverage",
                    "sourceId": "pilot_estimates",
                    "encodings": {
                        "x": {
                            "field": "model_short",
                            "type": "nominal",
                            "label": "Model",
                        },
                        "y": {
                            "field": "coverage",
                            "type": "quantitative",
                            "label": "Coverage",
                            "format": "percent",
                        },
                        "color": {"field": "component", "type": "nominal", "label": "Component"},
                    },
                    "yAxisTitle": "Configured coverage",
                    "valueFormat": "percent",
                    "layout": "full",
                },
                {
                    "id": "benchmark_scores",
                    "title": "Accepted benchmark evidence",
                    "subtitle": (
                        "Raw percent scores within explicit compatible cohorts; missing bars "
                        "are missing evidence."
                    ),
                    "type": "bar",
                    "dataset": "benchmarks",
                    "sourceId": "accepted_benchmarks",
                    "encodings": {
                        "x": {
                            "field": "model_short",
                            "type": "nominal",
                            "label": "Model",
                        },
                        "y": {"field": "score", "type": "quantitative", "label": "Raw score"},
                        "color": {
                            "field": "benchmark_short",
                            "type": "nominal",
                            "label": "Benchmark",
                        },
                    },
                    "yAxisTitle": "Source score (%)",
                    "valueFormat": "number",
                    "layout": "full",
                },
                {
                    "id": "effective_input_tokens",
                    "title": "Success-adjusted DeepSWE input use",
                    "subtitle": (
                        "Mean input tokens per attempt divided by observed task success; "
                        "lower is better."
                    ),
                    "type": "bar",
                    "dataset": "resources",
                    "sourceId": "accepted_efficiency",
                    "encodings": {
                        "x": {
                            "field": "model_short",
                            "type": "nominal",
                            "label": "Model",
                        },
                        "y": {
                            "field": "effective_input_tokens",
                            "type": "quantitative",
                            "label": "Effective input tokens",
                            "format": "compact",
                        },
                    },
                    "yAxisTitle": "Success-adjusted input tokens",
                    "valueFormat": "compact",
                    "layout": "full",
                },
                {
                    "id": "gap_counts",
                    "title": "Why the index is not yet headline-ready",
                    "subtitle": (
                        "All 70 configured model-by-capability cells, including absence and "
                        "rejected evidence."
                    ),
                    "type": "bar",
                    "dataset": "gap_counts",
                    "sourceId": "pilot_gaps",
                    "encodings": {
                        "x": {"field": "status", "type": "nominal", "label": "Evidence state"},
                        "y": {"field": "cells", "type": "quantitative", "label": "Cells"},
                    },
                    "yAxisTitle": "Configured cells",
                    "valueFormat": "number",
                    "layout": "full",
                },
            ],
            "tables": [],
            "sources": [
                {"id": source["id"], "label": source["label"], "path": source["path"]}
                for source in sources
            ],
            "blocks": [
                {
                    "id": "truth_status",
                    "type": "markdown",
                    "body": (
                        "## Current result: no headline UMI score\n\n"
                        "The pilot contains real, exact-configuration evidence, but **none "
                        "of the five models clears the Capability, Efficiency, Economics, "
                        "coverage, breadth, date, and readiness gates**. Partial estimates "
                        "below are diagnostic evidence views, "
                        "not a unified ranking."
                    ),
                    "sourceId": "pilot_estimates",
                },
                {
                    "id": "metrics",
                    "type": "metric-strip",
                    "cardIds": [
                        "pilot_scope",
                        "headline_state",
                        "capability_cells",
                        "coverage_ceiling",
                    ],
                },
                {"id": "coverage", "type": "chart", "chartId": "component_coverage"},
                {"id": "components", "type": "chart", "chartId": "component_scores"},
                {"id": "benchmarks", "type": "chart", "chartId": "benchmark_scores"},
                {
                    "id": "resources",
                    "type": "chart",
                    "chartId": "effective_input_tokens",
                },
                {"id": "gaps", "type": "chart", "chartId": "gap_counts"},
                {
                    "id": "method_note",
                    "type": "markdown",
                    "body": (
                        "## How to read this report\n\n"
                        "Compare raw benchmark values only within the displayed compatible cohort. "
                        "Compare normalized Capability values only when the evidence-profile "
                        "identifier matches. Efficiency currently represents one coding-agent "
                        "workload. Economics is absent because published DeepSWE cost and "
                        "wall-time facts do not verify the endpoint, service tier, cache policy, "
                        "and billing identity required for scoring."
                    ),
                },
            ],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": "2026-08-14T00:00:00Z",
            "status": "partial",
            "datasets": {
                "overview": overview,
                "model_summary": summary_rows,
                "component_scores": component_rows,
                "coverage": coverage_rows,
                "benchmarks": benchmark_rows,
                "resources": resource_rows,
                "gap_counts": gap_rows,
            },
            "accessIssues": [
                {
                    "id": "headline-blocked",
                    "scope": "Headline UMI",
                    "message": "No pilot model satisfies all configured publication gates.",
                },
                {
                    "id": "economics-missing",
                    "scope": "Economics",
                    "message": (
                        "No workload has endpoint-verified, scoring-ready Economics evidence."
                    ),
                },
                {
                    "id": "efficiency-sparse",
                    "scope": "Efficiency",
                    "message": "Efficiency covers one of six configured workload classes.",
                },
            ],
        },
        "sources": sources,
        "package_info": {
            "root": ".",
            "manifestPath": "data/pilots/v0.3/processed/pilot-dashboard.json",
            "snapshotPath": "data/pilots/v0.3/processed/pilot-dashboard.json",
        },
    }
