from __future__ import annotations

from collections import defaultdict

from umi._component import ComponentComputation, consolidate_numeric, weighted_available
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.normalize import normalize_cohort
from umi.schemas import BenchmarkMeasurement, ComponentScore, Domain, Provenance


def score_capability(dataset: Dataset, config: ProjectConfig) -> ComponentComputation:
    definitions = {item.id: item for item in config.benchmarks}
    grouped: dict[tuple[str, str, str], list[BenchmarkMeasurement]] = defaultdict(list)
    for item in dataset.benchmarks:
        grouped[(item.benchmark_id, item.cohort_key, item.model_id)].append(item)

    benchmark_scores: dict[str, dict[str, float | None]] = defaultdict(dict)
    benchmark_provisional: dict[str, bool] = {}
    selected_by_model: dict[str, list[Provenance]] = defaultdict(list)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    cohort_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for benchmark_id, cohort_key in sorted({(key[0], key[1]) for key in grouped}):
        definition = definitions[benchmark_id]
        raw: dict[str, float] = {}
        for (candidate_id, candidate_cohort, model_id), records in grouped.items():
            if candidate_id != benchmark_id or candidate_cohort != cohort_key:
                continue
            value, selected, conflict = consolidate_numeric(records, "value")
            if value is not None:
                raw[model_id] = value
                selected_by_model[model_id].extend(selected)
            if conflict:
                diagnostics[model_id].append(f"conflict consolidated for {benchmark_id}")
        normalized = normalize_cohort(
            raw,
            direction=definition.direction,
            strategy=definition.normalization,
            minimum_robust_cohort=config.normalization.minimum_robust_cohort,
            minimum_rank_cohort=config.normalization.minimum_rank_cohort,
        )
        for model_id, score in normalized.scores.items():
            if score is not None:
                cohort_scores[benchmark_id][model_id].append(score)
        benchmark_provisional[benchmark_id] = (
            benchmark_provisional.get(benchmark_id, False) or normalized.provisional
        )
    benchmark_scores = {
        benchmark_id: {model_id: sum(scores) / len(scores) for model_id, scores in by_model.items()}
        for benchmark_id, by_model in cohort_scores.items()
    }

    output: dict[str, ComponentScore] = {}
    model_domains: dict[str, tuple[Domain, ...]] = {}
    model_ids = [model.id for model in dataset.models]
    for model_id in model_ids:
        domain_values: dict[str, float | None] = {}
        represented: list[Domain] = []
        provisional = False
        available_family_weight = 0.0
        total_family_weight = 0.0
        families = {item.id: item for item in config.families}
        for domain in Domain:
            family_members: dict[str, list[str]] = defaultdict(list)
            for definition in config.benchmarks:
                if definition.domain == domain:
                    family_members[definition.family].append(definition.id)
            family_values: list[float] = []
            family_weights: list[float] = []
            for family_id, members in family_members.items():
                member_values = {
                    member: benchmark_scores.get(member, {}).get(model_id) for member in members
                }
                weights = {member: definitions[member].representation_weight for member in members}
                family_score, _ = weighted_available(member_values, weights)
                family = families[family_id]
                influence = min(family.weight, family.cap)
                total_family_weight += config.weights.capability_domains[domain] * influence
                if family_score is not None:
                    family_values.append(family_score)
                    family_weights.append(influence)
                    available_family_weight += config.weights.capability_domains[domain] * influence
                    provisional = provisional or any(
                        benchmark_provisional[member] for member in members
                    )
            if family_values:
                domain_values[domain.value] = sum(
                    value * weight
                    for value, weight in zip(family_values, family_weights, strict=True)
                ) / sum(family_weights)
                represented.append(domain)
            else:
                domain_values[domain.value] = None
        score, coverage = weighted_available(
            domain_values,
            {key.value: value for key, value in config.weights.capability_domains.items()},
        )
        evidence_records = tuple(
            {item.record_id: item for item in selected_by_model[model_id]}.values()
        )
        output[model_id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=provisional,
            source_record_ids=tuple(sorted(item.record_id for item in evidence_records)),
            diagnostics=tuple(sorted(diagnostics[model_id])),
            coverage_details={
                "capability_family_weighted": (
                    available_family_weight / total_family_weight if total_family_weight else 0.0
                ),
                "capability_families_represented": sum(
                    1
                    for family_id, members in {
                        family.id: [d.id for d in config.benchmarks if d.family == family.id]
                        for family in config.families
                    }.items()
                    if any(
                        benchmark_scores.get(member, {}).get(model_id) is not None
                        for member in members
                    )
                ),
                "capability_families_total": len(config.families),
            },
        )
        model_domains[model_id] = tuple(represented)
    return ComponentComputation(
        output, {key: tuple(value) for key, value in selected_by_model.items()}, model_domains
    )
