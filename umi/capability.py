from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from math import fsum

from umi._component import ComponentComputation, consolidate_numeric
from umi.config import ProjectConfig
from umi.evidence_profiles import capability_profile
from umi.loading import Dataset
from umi.normalize import build_score_scale, normalize_cohort
from umi.schemas import (
    BenchmarkContribution,
    BenchmarkDefinition,
    BenchmarkMeasurement,
    ComponentScore,
    Domain,
    EvidenceBenchmarkSeries,
    NormalizationPanel,
    Provenance,
    ScoreScale,
)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def representation_groups(
    config: ProjectConfig,
) -> dict[tuple[str, str], tuple[BenchmarkDefinition, ...]]:
    grouped: dict[tuple[str, str], list[BenchmarkDefinition]] = defaultdict(list)
    for definition in config.benchmarks:
        grouped[
            (definition.family, definition.representation_group or definition.id)
        ].append(definition)
    return {
        key: tuple(sorted(items, key=lambda item: item.selection_priority))
        for key, items in grouped.items()
    }


def canonical_representation_map(
    config: ProjectConfig,
) -> dict[str, tuple[BenchmarkDefinition, str]]:
    output: dict[str, tuple[BenchmarkDefinition, str]] = {}
    for (_, group_id), members in representation_groups(config).items():
        canonical = next(item for item in members if item.selection_priority == 0)
        for member in members:
            output[member.id] = (canonical, group_id)
    return output


def score_capability(
    dataset: Dataset,
    config: ProjectConfig,
    *,
    normalization_dataset: Dataset | None = None,
) -> ComponentComputation:
    """Score Capability on stable bundle-wide normalization panels."""
    panel_dataset = normalization_dataset or dataset
    definitions = {item.id: item for item in config.benchmarks}
    grouped_definitions = representation_groups(config)
    canonical_by_benchmark = canonical_representation_map(config)

    grouped: dict[
        tuple[str, str, str, str], dict[int, list[BenchmarkMeasurement]]
    ] = defaultdict(lambda: defaultdict(list))
    for item in panel_dataset.benchmarks:
        mapping = canonical_by_benchmark.get(item.benchmark_id)
        if mapping is None:
            continue
        canonical, group_id = mapping
        priority = definitions[item.benchmark_id].selection_priority
        grouped[(canonical.id, group_id, item.cohort_key, item.model_id)][priority].append(item)

    allowed_support = {
        (canonical.id, group_id, item.cohort_key, item.model_id)
        for item in dataset.benchmarks
        if (mapping := canonical_by_benchmark.get(item.benchmark_id)) is not None
        for canonical, group_id in (mapping,)
    }

    raw_by_series: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    selected: dict[tuple[str, str, str, str], tuple[BenchmarkMeasurement, ...]] = {}
    diagnostics: dict[str, list[str]] = defaultdict(list)
    for (benchmark_id, group_id, cohort_key, model_id), by_priority in sorted(grouped.items()):
        priority = min(by_priority)
        source_records = by_priority[priority]
        value, selected_records_list, conflict = consolidate_numeric(source_records, "value")
        if value is not None:
            raw_by_series[(benchmark_id, group_id, cohort_key)][model_id] = value
            selected[(benchmark_id, group_id, cohort_key, model_id)] = tuple(
                selected_records_list
            )
        if conflict:
            diagnostics[model_id].append(f"conflict consolidated for {benchmark_id}")

    normalized_scores: dict[tuple[str, str, str, str], float] = {}
    panels_by_series: dict[tuple[str, str, str], NormalizationPanel] = {}
    panels: dict[str, NormalizationPanel] = {}
    for (benchmark_id, group_id, cohort_key), raw in sorted(raw_by_series.items()):
        definition = definitions[benchmark_id]
        outcome = normalize_cohort(
            raw,
            direction=definition.direction,
            strategy=definition.normalization,
            minimum_robust_cohort=config.normalization.minimum_robust_cohort,
            minimum_rank_cohort=config.normalization.minimum_rank_cohort,
        )
        panel_records = tuple(
            record
            for model_id in sorted(raw)
            for record in sorted(
                selected[(benchmark_id, group_id, cohort_key, model_id)],
                key=lambda item: item.record_id,
            )
        )
        scored_input_fingerprint = _digest(
            [item.model_dump(mode="json") for item in panel_records]
        )
        panel_payload = {
            "benchmark_id": benchmark_id,
            "cohort_key": cohort_key,
            "canonical_representation_group": group_id,
            "model_ids": tuple(sorted(raw)),
            "cohort_roles": {model_id: "normalization_member" for model_id in sorted(raw)},
            "requested_strategy": definition.normalization,
            "applied_strategy": outcome.method,
            "cohort_size": len(raw),
            "transformation": "identity",
            "config_fingerprint": config.fingerprint,
            "scored_input_fingerprint": scored_input_fingerprint,
            "normalization_trace": outcome.trace,
        }
        panel = NormalizationPanel(
            id=_digest(panel_payload),
            benchmark_id=benchmark_id,
            cohort_key=cohort_key,
            canonical_representation_group=group_id,
            model_ids=tuple(sorted(raw)),
            cohort_roles={model_id: "normalization_member" for model_id in sorted(raw)},
            requested_strategy=definition.normalization,
            applied_strategy=outcome.method,
            cohort_size=len(raw),
            transformation="identity",
            config_fingerprint=config.fingerprint,
            scored_input_fingerprint=scored_input_fingerprint,
            normalization_trace=outcome.trace,
        )
        panels_by_series[(benchmark_id, group_id, cohort_key)] = panel
        panels[panel.id] = panel
        for model_id, value in outcome.scores.items():
            if value is not None:
                normalized_scores[(benchmark_id, group_id, cohort_key, model_id)] = value

    groups: list[tuple[Domain, str, str, float, BenchmarkDefinition]] = []
    for family in config.families:
        family_groups = {
            group_id: members
            for (family_id, group_id), members in grouped_definitions.items()
            if family_id == family.id
        }
        group_weights = {
            group_id: max(item.representation_weight for item in members)
            for group_id, members in family_groups.items()
        }
        total = fsum(group_weights.values())
        if total == 0:
            continue
        for group_id, members in family_groups.items():
            canonical = next(item for item in members if item.selection_priority == 0)
            groups.append(
                (
                    family.domain,
                    family.id,
                    group_id,
                    config.weights.capability_domains[family.domain]
                    * family.weight
                    * group_weights[group_id]
                    / total,
                    canonical,
                )
            )

    output: dict[str, ComponentScore] = {}
    evidence: dict[str, tuple[Provenance, ...]] = {}
    domains: dict[str, tuple[Domain, ...]] = {}
    contributions: dict[str, tuple[BenchmarkContribution, ...]] = {}
    scales: dict[str, ScoreScale] = {}
    for model in dataset.models:
        available: list[
            tuple[
                EvidenceBenchmarkSeries,
                float,
                float,
                float,
                tuple[BenchmarkMeasurement, ...],
                NormalizationPanel,
                BenchmarkDefinition,
            ]
        ] = []
        small_series: list[str] = []
        for domain, family_id, group_id, weight, definition in groups:
            matches = [
                (cohort, value)
                for (
                    benchmark_id,
                    candidate_group,
                    cohort,
                    model_id,
                ), value in normalized_scores.items()
                if benchmark_id == definition.id
                and candidate_group == group_id
                and model_id == model.id
                and (benchmark_id, candidate_group, cohort, model_id) in allowed_support
            ]
            if len(matches) != 1:
                continue
            cohort, normalized_value = matches[0]
            records_selected = selected[(definition.id, group_id, cohort, model.id)]
            raw_value = raw_by_series[(definition.id, group_id, cohort)][model.id]
            panel = panels_by_series[(definition.id, group_id, cohort)]
            series = EvidenceBenchmarkSeries(
                benchmark_id=definition.id,
                cohort_key=cohort,
                domain=domain,
                family=family_id,
                representation_group=group_id,
                signal_id=definition.signal_id or definition.id,
                budget_group=definition.budget_group or group_id,
            )
            available.append(
                (
                    series,
                    weight,
                    normalized_value,
                    raw_value,
                    records_selected,
                    panel,
                    definition,
                )
            )
            if panel.normalization_trace.provisional:
                small_series.append(f"{definition.id}/{cohort}")
        coverage = fsum(item[1] for item in available)
        score = fsum(item[1] * item[2] for item in available) / coverage if coverage else None
        evidence_records = tuple(
            {
                record.record_id: record
                for *_, records_selected, _panel, _definition in available
                for record in records_selected
            }.values()
        )
        profile = (
            capability_profile((item[0] for item in available), evidence_records, config)
            if available
            else None
        )
        model_panel_ids = tuple(sorted({item[5].id for item in available}))
        scale = (
            build_score_scale(profile.id, model_panel_ids, config.fingerprint)
            if profile is not None and score is not None
            else None
        )
        if scale is not None:
            scales[model.id] = scale
        model_contributions = tuple(
            BenchmarkContribution(
                benchmark_id=series.benchmark_id,
                cohort_key=series.cohort_key,
                raw_value=raw_value,
                raw_unit=definition.unit,
                direction=definition.direction,
                source_uncertainty=(
                    records_selected[0].uncertainty if len(records_selected) == 1 else None
                ),
                configured_absolute_weight=weight,
                requested_normalization=definition.normalization,
                applied_normalization=panel.applied_strategy,
                normalization_panel_id=panel.id,
                normalized_value=normalized_value,
                weighted_contribution=weight * normalized_value,
                normalization_trace=panel.normalization_trace,
                source_record_ids=tuple(sorted(item.record_id for item in records_selected)),
            )
            for (
                series,
                weight,
                normalized_value,
                raw_value,
                records_selected,
                panel,
                definition,
            ) in available
        )
        contributions[model.id] = model_contributions
        if small_series:
            diagnostics[model.id].append(
                "provisional normalization cohorts: " + ", ".join(sorted(small_series))
            )
        represented_domains = tuple(
            sorted({item[0].domain for item in available}, key=lambda item: item.value)
        )
        output[model.id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=bool(small_series),
            source_record_ids=tuple(sorted(item.record_id for item in evidence_records)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
            coverage_details={
                "capability_total_weighted": coverage,
                "capability_families_represented": len({item[0].family for item in available}),
                "capability_families_total": len(config.families),
                "capability_representations_represented": len(available),
                "capability_representations_total": len(groups),
            },
            evidence_profile=profile,
            evidence_profile_id=profile.id if profile is not None else None,
            normalization_panel_ids=model_panel_ids,
            score_scale_id=scale.id if scale is not None else None,
            score_semantics=(
                "stable-panel percentile position"
                if len(available) == 1
                else "weighted stable-panel percentile composite"
                if available
                else "unscored"
            ),
        )
        evidence[model.id] = evidence_records
        domains[model.id] = represented_domains

    for model_id, component in output.items():
        has_support = (
            component.score is not None
            and component.evidence_profile_id is not None
            and component.score_scale_id is not None
        )
        peers = tuple(
            sorted(
                other_id
                for other_id, other in output.items()
                if has_support
                and other_id != model_id
                and other.evidence_profile_id == component.evidence_profile_id
                and other.score_scale_id == component.score_scale_id
            )
        )
        output[model_id] = component.model_copy(
            update={
                "directly_comparable_model_ids": peers,
                "comparability_status": (
                    "directly_comparable"
                    if peers
                    else "different_score_scale"
                    if has_support
                    else "insufficient_common_support"
                ),
                "comparability_reasons": (
                    (
                        "same evidence profile, score scale, formula, normalization, and "
                        "configuration",
                    )
                    if peers
                    else ("no other model shares both evidence profile and score scale",)
                    if has_support
                    else ("no ready capability benchmark support",)
                ),
            }
        )
    return ComponentComputation(output, evidence, domains, panels, contributions, scales)
