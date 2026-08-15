from __future__ import annotations

import hashlib
import itertools
import json

from scipy.stats import rankdata

from umi.capability import canonical_representation_map, score_capability
from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.readiness import scoring_dataset
from umi.schemas import (
    BenchmarkDefinition,
    BenchmarkMeasurement,
    CapabilityComparisonResult,
    ComparisonModelScore,
    ComparisonStatus,
    RankRobustness,
    RawBenchmarkResult,
    SensitivityInterval,
    Unit,
)
from umi.validation import validate_dataset

SeriesKey = tuple[str, str, str]


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _filter_common_dataset(
    dataset: Dataset,
    requested: tuple[str, ...],
    common: set[SeriesKey],
    canonical: dict[str, tuple[BenchmarkDefinition, str]],
) -> Dataset:
    return dataset.model_copy(
        update={
            "models": tuple(item for item in dataset.models if item.id in requested),
            "benchmarks": tuple(
                item
                for item in dataset.benchmarks
                if item.model_id in requested
                and (
                    canonical[item.benchmark_id][0].id,
                    canonical[item.benchmark_id][1],
                    item.cohort_key,
                )
                in common
            ),
            "efficiency": (),
            "task_economics": (),
        }
    )


def _interval(
    record: BenchmarkMeasurement,
    unit: Unit,
) -> SensitivityInterval | None:
    uncertainty = record.uncertainty
    if uncertainty is None:
        return None
    assumption = None
    z_value = None
    if uncertainty.lower is not None and uncertainty.upper is not None:
        lower, upper = uncertainty.lower, uncertainty.upper
        origin = "source_bounds"
    elif uncertainty.margin is not None:
        lower = record.value - uncertainty.margin
        upper = record.value + uncertainty.margin
        origin = "published_margin"
    elif uncertainty.standard_error is not None:
        z_value = 1.96
        lower = record.value - z_value * uncertainty.standard_error
        upper = record.value + z_value * uncertainty.standard_error
        origin = "derived_from_standard_error"
        assumption = "normal_approximation"
    else:
        return None
    if unit == Unit.PERCENT:
        lower, upper = max(0.0, lower), min(100.0, upper)
    return SensitivityInterval(
        record_id=record.record_id,
        model_id=record.model_id,
        benchmark_id=record.benchmark_id,
        lower=lower,
        upper=upper,
        interval_origin=origin,
        assumption=assumption,
        z_value=z_value,
    )


def _rank_robustness(
    scored: Dataset,
    config: ProjectConfig,
    requested: tuple[str, ...],
    common: set[SeriesKey],
    central_scores: dict[str, float],
    central_ranks: dict[str, float],
    contribution_ids: set[str],
    canonical: dict[str, tuple[BenchmarkDefinition, str]],
) -> tuple[dict[str, RankRobustness], tuple[SensitivityInterval, ...]]:
    definitions = {item.id: item for item in config.benchmarks}
    records = {item.record_id: item for item in scored.benchmarks}
    intervals = tuple(
        interval
        for record_id in sorted(contribution_ids)
        if (record := records.get(record_id)) is not None
        if (
            interval := _interval(
                record,
                definitions[record.benchmark_id].unit,
            )
        )
        is not None
    )
    exhaustive = len(intervals) <= 12
    corners = (
        itertools.product((0, 1), repeat=len(intervals))
        if exhaustive
        else ((),)
    )
    scenario_scores: dict[str, list[float]] = {model_id: [] for model_id in requested}
    scenario_ranks: dict[str, list[float]] = {model_id: [] for model_id in requested}
    dominance: dict[tuple[str, str], bool] = {
        (left, right): True
        for left in requested
        for right in requested
        if left != right
    }
    scenario_count = 0
    for corner in corners:
        replacements = {
            item.record_id: (item.lower, item.upper)[endpoint]
            for item, endpoint in zip(intervals, corner, strict=True)
        }
        modified = scored.model_copy(
            update={
                "benchmarks": tuple(
                    item.model_copy(update={"value": replacements[item.record_id]})
                    if item.record_id in replacements
                    else item
                    for item in scored.benchmarks
                )
            }
        )
        scenario_filtered = _filter_common_dataset(modified, requested, common, canonical)
        computation = score_capability(
            scenario_filtered,
            config,
            normalization_dataset=modified,
        )
        scores = {
            model_id: computation.components[model_id].score for model_id in requested
        }
        if any(value is None for value in scores.values()):
            continue
        numeric = {key: float(value) for key, value in scores.items() if value is not None}
        ranks = rankdata([-numeric[key] for key in requested], method="average")
        for model_id, rank in zip(requested, ranks, strict=True):
            scenario_scores[model_id].append(numeric[model_id])
            scenario_ranks[model_id].append(float(rank))
        for left, right in dominance:
            dominance[(left, right)] = dominance[(left, right)] and (
                numeric[left] > numeric[right]
            )
        scenario_count += 1
    if scenario_count == 0:
        scenario_count = 1
        for model_id in requested:
            scenario_scores[model_id] = [central_scores[model_id]]
            scenario_ranks[model_id] = [central_ranks[model_id]]
    assumptions = [
        "joint lower/upper corner enumeration",
        "scenario counts are not probabilities",
        "stable normalization panel membership held fixed",
    ]
    if any(item.interval_origin == "derived_from_standard_error" for item in intervals):
        assumptions.append("standard-error intervals use a normal approximation with z=1.96")
    output = {
        model_id: RankRobustness(
            central_estimate_rank=central_ranks[model_id],
            possible_rank_min=min(scenario_ranks[model_id]),
            possible_rank_max=max(scenario_ranks[model_id]),
            possible_ranks=tuple(sorted(set(scenario_ranks[model_id]))),
            central_composite_score=central_scores[model_id],
            composite_score_min=min(scenario_scores[model_id]),
            composite_score_max=max(scenario_scores[model_id]),
            robustly_dominates=tuple(
                sorted(
                    other
                    for other in requested
                    if other != model_id and dominance[(model_id, other)]
                )
            ),
            robustly_dominated_by=tuple(
                sorted(
                    other
                    for other in requested
                    if other != model_id and dominance[(other, model_id)]
                )
            ),
            scenario_count=scenario_count,
            exhaustive=exhaustive,
            uncertainty_mode=(
                "deterministic_joint_endpoint_enumeration"
                if exhaustive
                else "not_enumerated_over_12_uncertain_records"
            ),
            assumptions=tuple(assumptions),
        )
        for model_id in requested
    }
    return output, intervals


def common_capability_comparison(
    dataset: Dataset, config: ProjectConfig, model_ids: tuple[str, ...]
) -> dict[str, object]:
    """Compare raw common evidence on bundle-wide stable normalization panels."""
    if len(model_ids) < 2 or len(set(model_ids)) != len(model_ids):
        raise ValueError("compare requires at least two distinct model IDs")
    validate_dataset(dataset, config).raise_for_errors()
    scored, _ = scoring_dataset(dataset)
    requested = tuple(sorted(model_ids))
    known = {model.id for model in scored.models}
    missing = sorted(set(requested) - known)
    if missing:
        raise ValueError("unknown comparison model IDs: " + ", ".join(missing))
    canonical = canonical_representation_map(config)
    available = {
        model_id: {
            (
                canonical[item.benchmark_id][0].id,
                canonical[item.benchmark_id][1],
                item.cohort_key,
            )
            for item in scored.benchmarks
            if item.model_id == model_id
        }
        for model_id in requested
    }
    common = set.intersection(*available.values())
    group_id = _digest(
        {"models": requested, "series": sorted(common), "config": config.fingerprint}
    )
    if not common:
        union = set.union(*available.values())
        by_group: dict[tuple[str, str], dict[str, set[str]]] = {}
        for model_id, series in available.items():
            for benchmark_id, representation_group, cohort_key in series:
                by_group.setdefault((benchmark_id, representation_group), {}).setdefault(
                    model_id, set()
                ).add(cohort_key)
        incompatible = tuple(
            sorted(
                f"{benchmark_id}/{representation_group}"
                for (benchmark_id, representation_group), cohorts_by_model in by_group.items()
                if set(cohorts_by_model) == set(requested)
                and not set.intersection(*cohorts_by_model.values())
            )
        )
        missing_by_model = {
            model_id: tuple(
                "/".join(series)
                for series in sorted(union - available[model_id])
            )
            for model_id in requested
        }
        recommended = tuple(
            sorted(
                f"{model_id}: {series}"
                for model_id, series_list in missing_by_model.items()
                for series in series_list
            )
        )
        return CapabilityComparisonResult(
            status=ComparisonStatus.INSUFFICIENT_COMMON_SUPPORT,
            comparison_group_id=group_id,
            comparison_model_ids=requested,
            missing_support_by_model=missing_by_model,
            incompatible_series=incompatible,
            recommended_missing_evidence=recommended,
            normalization_method="not applied",
            primary_result_semantics="raw benchmark metrics",
            publication_label="abstained — insufficient common evidence",
        ).model_dump(mode="json")

    filtered = _filter_common_dataset(scored, requested, common, canonical)
    computation = score_capability(filtered, config, normalization_dataset=scored)
    components = computation.components
    profile_ids = {components[item].evidence_profile_id for item in requested}
    scale_ids = {components[item].score_scale_id for item in requested}
    profile_id = next(iter(profile_ids)) if len(profile_ids) == 1 else None
    scale_id = next(iter(scale_ids)) if len(scale_ids) == 1 else None
    if profile_id is None or scale_id is None:
        raise ValueError("common comparison failed to produce one evidence profile and score scale")
    central_scores: dict[str, float] = {}
    for model_id in requested:
        value = components[model_id].score
        if value is None:
            raise ValueError("common comparison produced an unscored model")
        central_scores[model_id] = value
    central_rank_values = rankdata(
        [-central_scores[model_id] for model_id in requested], method="average"
    )
    central_ranks = {
        model_id: float(rank)
        for model_id, rank in zip(requested, central_rank_values, strict=True)
    }
    contribution_ids = {
        record_id
        for model_id in requested
        for contribution in computation.contributions[model_id]
        for record_id in contribution.source_record_ids
    }
    robustness, intervals = _rank_robustness(
        scored,
        config,
        requested,
        common,
        central_scores,
        central_ranks,
        contribution_ids,
        canonical,
    )
    scores = tuple(
        ComparisonModelScore(
            model_id=model_id,
            score=central_scores[model_id],
            normalized_composite_score=central_scores[model_id],
            coverage=components[model_id].coverage,
            provisional=components[model_id].provisional,
            rank=central_ranks[model_id],
            evidence_profile_id=profile_id,
            normalization_panel_ids=components[model_id].normalization_panel_ids,
            score_scale_id=scale_id,
            score_semantics=components[model_id].score_semantics,
            primary_raw_results=tuple(
                RawBenchmarkResult(
                    benchmark_id=item.benchmark_id,
                    cohort_key=item.cohort_key,
                    raw_value=item.raw_value,
                    raw_unit=item.raw_unit,
                    direction=item.direction,
                    source_uncertainty=item.source_uncertainty,
                )
                for item in computation.contributions[model_id]
            ),
            contributions=computation.contributions[model_id],
            rank_robustness=robustness[model_id],
        )
        for model_id in requested
    )
    panel_ids = sorted(
        {
            panel_id
            for model_id in requested
            for panel_id in components[model_id].normalization_panel_ids
        }
    )
    result = CapabilityComparisonResult(
        status=ComparisonStatus.OK,
        comparison_group_id=group_id,
        comparison_model_ids=requested,
        common_evidence_profile_id=profile_id,
        common_benchmark_series=tuple(
            {
                "benchmark_id": benchmark_id,
                "canonical_representation_group": representation_group,
                "cohort_key": cohort_key,
            }
            for benchmark_id, representation_group, cohort_key in sorted(common)
        ),
        scores=scores,
        normalization_panels=tuple(
            computation.normalization_panels[panel_id] for panel_id in panel_ids
        ),
        score_scale=computation.score_scales[requested[0]],
        normalization_method="bundle-wide stable panel per canonical benchmark series",
        primary_result_semantics="raw benchmark metrics",
        sensitivity_intervals=intervals,
        publication_label="real evidence, provisional common-evidence comparison",
    )
    return result.model_dump(mode="json")
