from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric
from umi.config import ProjectConfig
from umi.evidence_profiles import capability_profile
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import (
    BenchmarkMeasurement,
    ComponentScore,
    Domain,
    EvidenceBenchmarkSeries,
    Provenance,
)


def score_capability(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    """Score with one flattened configured weight per representation group."""
    definitions = {item.id: item for item in config.benchmarks}
    grouped: dict[tuple[str, str, str], list[BenchmarkMeasurement]] = defaultdict(list)
    for item in dataset.benchmarks:
        grouped[(item.benchmark_id, item.cohort_key, item.model_id)].append(item)

    scores: dict[tuple[str, str, str], float] = {}
    selected: dict[tuple[str, str, str], tuple[Provenance, ...]] = {}
    provisional: set[tuple[str, str, str]] = set()
    diagnostics: dict[str, list[str]] = defaultdict(list)
    for benchmark_id, cohort_key in sorted({key[:2] for key in grouped}):
        raw: dict[str, float] = {}
        for (candidate, cohort, model_id), source_records in grouped.items():
            if (candidate, cohort) != (benchmark_id, cohort_key):
                continue
            value, records_selected, conflict = consolidate_numeric(source_records, "value")
            if value is not None:
                raw[model_id] = value
                selected[(benchmark_id, cohort_key, model_id)] = tuple(records_selected)
            if conflict:
                diagnostics[model_id].append(f"conflict consolidated for {benchmark_id}")
        outcome = normalize_cohort(
            raw,
            direction=definitions[benchmark_id].direction,
            strategy=definitions[benchmark_id].normalization,
            minimum_robust_cohort=config.normalization.minimum_robust_cohort,
            minimum_rank_cohort=config.normalization.minimum_rank_cohort,
        )
        for model_id, value in outcome.scores.items():
            if value is not None:
                scores[(benchmark_id, cohort_key, model_id)] = value
                if outcome.provisional:
                    provisional.add((benchmark_id, cohort_key, model_id))

    groups: list[tuple[Domain, str, str, float, str]] = []
    for family in config.families:
        members = [item for item in config.benchmarks if item.family == family.id]
        by_group: dict[str, list[str]] = defaultdict(list)
        for member in members:
            by_group[member.representation_group or member.id].append(member.id)
        group_weights = {
            group_id: max(definitions[item].representation_weight for item in aliases)
            for group_id, aliases in by_group.items()
        }
        total = sum(group_weights.values())
        if total == 0:
            continue
        for group_id, aliases in by_group.items():
            canonical = min(aliases)
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
    for model in dataset.models:
        available: list[tuple[EvidenceBenchmarkSeries, float, float, tuple[Provenance, ...]]] = []
        small_series: list[str] = []
        for domain, family_id, group_id, weight, benchmark_id in groups:
            matches = [
                (cohort, value)
                for (candidate, cohort, model_id), value in scores.items()
                if candidate == benchmark_id and model_id == model.id
            ]
            if len(matches) != 1:
                continue
            cohort, value = matches[0]
            series = EvidenceBenchmarkSeries(
                benchmark_id=benchmark_id,
                cohort_key=cohort,
                domain=domain,
                family=family_id,
                representation_group=group_id,
                signal_id=benchmark_id,
                budget_group=group_id,
            )
            selected_records = selected[(benchmark_id, cohort, model.id)]
            available.append((series, weight, value, selected_records))
            if (benchmark_id, cohort, model.id) in provisional:
                small_series.append(f"{benchmark_id}/{cohort}")
        coverage = sum(item[1] for item in available)
        score = sum(item[1] * item[2] for item in available) / coverage if coverage else None
        evidence_records = tuple(
            {
                record.record_id: record
                for *_, selected_records in available
                for record in selected_records
            }.values()
        )
        profile = capability_profile((item[0] for item in available), evidence_records, config)
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
        )
        evidence[model.id] = evidence_records
        domains[model.id] = represented_domains

    for model_id, component in output.items():
        profile_id = component.evidence_profile.id if component.evidence_profile else None
        peers = tuple(
            sorted(
                other_id
                for other_id, other in output.items()
                if other_id != model_id
                and other.evidence_profile
                and other.evidence_profile.id == profile_id
            )
        )
        output[model_id] = component.model_copy(
            update={
                "directly_comparable_model_ids": peers,
                "comparability_status": (
                    "directly_comparable" if peers else "different_evidence_profile"
                ),
                "comparability_reasons": (
                    ("same capability support series and configuration",)
                    if peers
                    else ("no other model has the same capability evidence profile",)
                ),
            }
        )
    return ComponentComputation(output, evidence, domains)
