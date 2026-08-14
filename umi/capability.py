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

    benchmark_scores: dict[str, dict[str, float]] = defaultdict(dict)
    provisional_cohorts: set[tuple[str, str, str]] = set()
    selected_by_model: dict[str, list[Provenance]] = defaultdict(list)
    diagnostics: dict[str, list[str]] = defaultdict(list)
    series = sorted({(benchmark_id, cohort_key) for benchmark_id, cohort_key, _ in grouped})
    for benchmark_id, cohort_key in series:
        definition = definitions[benchmark_id]
        raw: dict[str, float] = {}
        for (candidate_id, candidate_cohort, model_id), records in grouped.items():
            if (candidate_id, candidate_cohort) != (benchmark_id, cohort_key):
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
                benchmark_scores[benchmark_id][model_id] = score
                if normalized.provisional:
                    provisional_cohorts.add((benchmark_id, cohort_key, model_id))

    output: dict[str, ComponentScore] = {}
    model_domains: dict[str, tuple[Domain, ...]] = {}
    total_representation_groups = len(
        {
            (item.family, item.representation_group or item.id)
            for item in config.benchmarks
        }
    )
    for model in dataset.models:
        domain_values: dict[str, float | None] = {}
        domain_coverage: dict[Domain, float] = {}
        represented_domains: list[Domain] = []
        represented_families = 0
        represented_groups = 0
        provisional_ids: set[str] = set()

        for domain in Domain:
            family_values: dict[str, float | None] = {}
            family_weights: dict[str, float] = {}
            coverage_value = 0.0
            for family in (item for item in config.families if item.domain == domain):
                members = [item for item in config.benchmarks if item.family == family.id]
                groups: dict[str, list[str]] = defaultdict(list)
                for member in members:
                    groups[member.representation_group or member.id].append(member.id)
                group_values: dict[str, float | None] = {}
                group_weights: dict[str, float] = {}
                for group_id, aliases in groups.items():
                    values: list[float] = []
                    for alias in aliases:
                        alias_value = benchmark_scores.get(alias, {}).get(model.id)
                        if alias_value is not None:
                            values.append(alias_value)
                    group_values[group_id] = sum(values) / len(values) if values else None
                    group_weights[group_id] = max(
                        definitions[alias].representation_weight for alias in aliases
                    )
                    if values:
                        represented_groups += 1
                        for alias in aliases:
                            for benchmark_id, cohort_key, model_id in provisional_cohorts:
                                if alias == benchmark_id and model_id == model.id:
                                    provisional_ids.add(f"{benchmark_id}/{cohort_key}")
                family_score, family_coverage = weighted_available(group_values, group_weights)
                family_values[family.id] = family_score
                family_weights[family.id] = family.weight
                coverage_value += family.weight * family_coverage
                if family_score is not None:
                    represented_families += 1
            domain_score, _ = weighted_available(family_values, family_weights)
            domain_values[domain.value] = domain_score
            domain_coverage[domain] = coverage_value
            if domain_score is not None:
                represented_domains.append(domain)

        score, _ = weighted_available(
            domain_values,
            {key.value: value for key, value in config.weights.capability_domains.items()},
        )
        coverage = sum(
            config.weights.capability_domains[domain] * domain_coverage.get(domain, 0.0)
            for domain in config.weights.capability_domains
        )
        if provisional_ids:
            diagnostics[model.id].append(
                "provisional normalization cohorts: " + ", ".join(sorted(provisional_ids))
            )
        evidence_records = tuple(
            {item.record_id: item for item in selected_by_model[model.id]}.values()
        )
        output[model.id] = ComponentScore(
            score=score,
            coverage=coverage,
            provisional=bool(provisional_ids),
            source_record_ids=tuple(sorted(item.record_id for item in evidence_records)),
            diagnostics=tuple(sorted(set(diagnostics[model.id]))),
            coverage_details={
                "capability_domain_weighted": coverage,
                "capability_family_weighted": coverage,
                "capability_representation_weighted": coverage,
                "capability_families_represented": represented_families,
                "capability_families_total": len(config.families),
                "capability_representations_represented": represented_groups,
                "capability_representations_total": total_representation_groups,
            },
        )
        model_domains[model.id] = tuple(represented_domains)
    return ComponentComputation(
        output, {key: tuple(value) for key, value in selected_by_model.items()}, model_domains
    )
