from __future__ import annotations

from typing import TYPE_CHECKING, cast

from umi._component import weighted_available
from umi.capability import score_capability
from umi.config import OverallWeights, ProjectConfig
from umi.economics import score_economics
from umi.efficiency import score_efficiency
from umi.fingerprints import dataset_fingerprint, scored_data_fingerprint
from umi.loading import Dataset
from umi.provenance import independent_or_community_evidence_share
from umi.readiness import ScoredRecord, evidence_date, is_scoring_ready, scoring_dataset
from umi.schemas import Confidence, CoverageSummary, Domain, ScoringResult
from umi.validation import validate_dataset
from umi.value import value_score
from umi.version import ENGINE_VERSION, FORMULA_VERSION, NORMALIZATION_VERSION

if TYPE_CHECKING:
    from umi.bundle import ScoringBundle


def overall_for_weights(result: ScoringResult, weights: OverallWeights) -> float | None:
    score, _ = weighted_available(
        {
            "capability": result.capability.score,
            "efficiency": result.efficiency.score,
            "economics": result.economics.score,
        },
        {
            "capability": weights.capability,
            "efficiency": weights.efficiency,
            "economics": weights.economics,
        },
    )
    return score


def weighted_overall_coverage(result: ScoringResult, weights: OverallWeights) -> float:
    return (
        weights.capability * result.capability.coverage
        + weights.efficiency * result.efficiency.coverage
        + weights.economics * result.economics.coverage
    )


def eligible_for_weights(
    result: ScoringResult, config: ProjectConfig, weights: OverallWeights
) -> bool:
    minimum = config.eligibility.minimum_component_coverage
    return (
        result.scoring_ready
        and result.capability.score is not None
        and result.efficiency.score is not None
        and result.economics.score is not None
        and result.capability.coverage >= minimum["capability"]
        and result.efficiency.coverage >= minimum["efficiency"]
        and result.economics.coverage >= minimum["economics"]
        and weighted_overall_coverage(result, weights)
        >= config.eligibility.minimum_overall_coverage
        and len(result.capability_domains) >= config.eligibility.minimum_capability_domains
        and float(result.efficiency.coverage_details.get("efficiency_workload_weighted", 0.0))
        >= config.eligibility.minimum_efficiency_workload_coverage
        and config.eligibility.release_start
        <= result.release_date
        <= config.eligibility.release_end
    )


def score_dataset(
    dataset: Dataset, config: ProjectConfig, *, allow_unready: bool = False
) -> list[ScoringResult]:
    report = validate_dataset(dataset, config)
    report.raise_for_errors()
    scored_dataset, _ = scoring_dataset(dataset, allow_unready=allow_unready)
    capability = score_capability(scored_dataset, config)
    efficiency = score_efficiency(scored_dataset, config)
    economics = score_economics(scored_dataset, config)
    weights = config.weights.overall
    complete_fingerprint = dataset_fingerprint(dataset, config)
    scored_fingerprint = scored_data_fingerprint(scored_dataset, config)
    cohort_model_ids = tuple(sorted(model.id for model in scored_dataset.models))
    scored_observations: tuple[ScoredRecord, ...] = (
        *scored_dataset.benchmarks,
        *scored_dataset.efficiency,
        *scored_dataset.task_economics,
    )
    observed_dates = [
        item_date
        for item in scored_observations
        if (item_date := evidence_date(item))
    ]
    data_as_of = max(observed_dates) if observed_dates else config.eligibility.release_end
    models = {model.id: model for model in scored_dataset.models}
    baseline_value = config.value.baseline_scenario
    results: list[ScoringResult] = []

    for model in sorted(scored_dataset.models, key=lambda item: item.id):
        cap = capability.components[model.id]
        eff = efficiency.components[model.id]
        econ = economics.components[model.id]
        partial, _ = weighted_available(
            {
                "capability": cap.score,
                "efficiency": eff.score,
                "economics": econ.score,
            },
            {
                "capability": weights.capability,
                "efficiency": weights.efficiency,
                "economics": weights.economics,
            },
        )
        overall_coverage = (
            weights.capability * cap.coverage
            + weights.efficiency * eff.coverage
            + weights.economics * econ.coverage
        )
        records_by_id: dict[str, ScoredRecord] = {}
        for record in (
            *capability.evidence.get(model.id, ()),
            *efficiency.evidence.get(model.id, ()),
            *economics.evidence.get(model.id, ()),
        ):
            records_by_id[record.record_id] = cast(ScoredRecord, record)
        component_quality = {
            "capability": independent_or_community_evidence_share(
                capability.evidence.get(model.id, ())
            ),
            "efficiency": independent_or_community_evidence_share(
                efficiency.evidence.get(model.id, ())
            ),
            "economics": independent_or_community_evidence_share(
                economics.evidence.get(model.id, ())
            ),
        }
        quality_numerator = (
            weights.capability * cap.coverage * component_quality["capability"]
            + weights.efficiency * eff.coverage * component_quality["efficiency"]
            + weights.economics * econ.coverage * component_quality["economics"]
        )
        quality = quality_numerator / overall_coverage if overall_coverage else 0.0
        selected_unready = [
            record.record_id
            for record in records_by_id.values()
            if not is_scoring_ready(record, models[model.id])
        ]
        scoring_ready = not selected_unready
        domains = capability.domains.get(model.id, ())
        efficiency_workload_coverage = float(
            eff.coverage_details.get("efficiency_workload_weighted", 0.0)
        )
        component_minimum = config.eligibility.minimum_component_coverage
        eligible = (
            scoring_ready
            and cap.score is not None
            and eff.score is not None
            and econ.score is not None
            and cap.coverage >= component_minimum["capability"]
            and eff.coverage >= component_minimum["efficiency"]
            and econ.coverage >= component_minimum["economics"]
            and overall_coverage >= config.eligibility.minimum_overall_coverage
            and len(domains) >= config.eligibility.minimum_capability_domains
            and efficiency_workload_coverage
            >= config.eligibility.minimum_efficiency_workload_coverage
            and config.eligibility.release_start
            <= model.release_date
            <= config.eligibility.release_end
        )
        provisional = not eligible or cap.provisional or eff.provisional or econ.provisional
        if (
            overall_coverage >= config.eligibility.high_confidence_coverage
            and quality >= config.eligibility.high_confidence_quality_share
        ):
            confidence = Confidence.HIGH
        elif (
            overall_coverage >= config.eligibility.medium_confidence_coverage
            and quality >= config.eligibility.medium_confidence_quality_share
        ):
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW
        organizations = {record.source.organization for record in records_by_id.values()}
        all_diagnostics = {*cap.diagnostics, *eff.diagnostics, *econ.diagnostics}
        confidence_reasons = [
            f"{overall_coverage:.0%} hierarchical weighted coverage",
            f"{len(domains)}/{len(Domain)} capability domains represented",
            (
                f"{int(eff.coverage_details.get('efficiency_workloads_represented', 0))}/"
                f"{len(config.weights.workload_weights)} efficiency workload classes"
            ),
            f"{len(organizations)} source organizations",
            f"{quality:.0%} independent/community evidence",
        ]
        if not eligible:
            confidence = Confidence.LOW
            confidence_reasons.append("confidence forced to Low: headline eligibility failed")
        if provisional:
            confidence_reasons.append("one or more contributing results are provisional")
            if confidence == Confidence.HIGH:
                confidence = Confidence.MEDIUM
                confidence_reasons.append("confidence capped at Medium: provisional normalization")
        if any("conflict" in item for item in all_diagnostics):
            confidence_reasons.append("selected evidence contains an unresolved conflict")
            if confidence == Confidence.HIGH:
                confidence = Confidence.MEDIUM
                confidence_reasons.append(
                    "confidence capped at Medium: selected-evidence conflict"
                )
        if len(organizations) < 2:
            confidence_reasons.append("evidence depends on one source organization")
            if confidence == Confidence.HIGH:
                confidence = Confidence.MEDIUM
                confidence_reasons.append("confidence capped at Medium: single-source dependence")
        if records_by_id and quality == 0:
            confidence_reasons.append("selected evidence is vendor-reported or derived only")
        if len(domains) < config.eligibility.minimum_capability_domains:
            confidence = Confidence.LOW
            confidence_reasons.append("confidence forced to Low: insufficient capability breadth")
        if selected_unready:
            confidence = Confidence.LOW
            confidence_reasons.append("confidence forced to Low: unready evidence override used")
        diagnostics = sorted(
            {
                *all_diagnostics,
                *([] if eligible else ["not eligible for headline Overall ranking"]),
                *(
                    ["unready evidence override used: " + ", ".join(sorted(selected_unready))]
                    if selected_unready
                    else []
                ),
                *(
                    ["model release date is outside the configured eligibility window"]
                    if not (
                        config.eligibility.release_start
                        <= model.release_date
                        <= config.eligibility.release_end
                    )
                    else []
                ),
            }
        )
        result = ScoringResult(
            model_id=model.id,
            publication_label=(
                "synthetic demonstration — not a real model ranking"
                if model.synthetic
                else "real evidence — model-specific partial estimate"
            ),
            release_date=model.release_date,
            capability=cap,
            efficiency=eff,
            economics=econ,
            partial_overall_estimate=partial,
            headline_overall=partial if eligible else None,
            value=value_score(
                cap.score,
                econ.score,
                baseline_value.formula,
                baseline_value.alpha if baseline_value.alpha is not None else 0.5,
            ),
            value_scenario=baseline_value.name,
            value_formula=baseline_value.formula,
            value_parameters=(
                {"alpha": baseline_value.alpha} if baseline_value.alpha is not None else {}
            ),
            overall_coverage=overall_coverage,
            confidence=confidence,
            eligible=eligible,
            scoring_ready=scoring_ready,
            provisional=provisional,
            capability_domains=domains,
            independent_or_community_evidence_share=quality,
            source_record_ids=tuple(sorted(records_by_id)),
            diagnostics=tuple(diagnostics),
            confidence_reasons=tuple(confidence_reasons),
            coverage=CoverageSummary(
                overall_weighted=overall_coverage,
                capability_domains_represented=len(domains),
                capability_domains_total=len(Domain),
                capability_absolute_weighted=float(
                    cap.coverage_details.get("capability_total_weighted", 0.0)
                ),
                capability_families_represented=int(
                    cap.coverage_details.get("capability_families_represented", 0)
                ),
                capability_families_total=len(config.families),
                capability_representations_represented=int(
                    cap.coverage_details.get("capability_representations_represented", 0)
                ),
                capability_representations_total=int(
                    cap.coverage_details.get("capability_representations_total", 0)
                ),
                efficiency_workloads_represented=int(
                    eff.coverage_details.get("efficiency_workloads_represented", 0)
                ),
                efficiency_workloads_total=len(config.weights.workload_weights),
                efficiency_workload_weighted=efficiency_workload_coverage,
                efficiency_metric_weighted=float(
                    eff.coverage_details.get("efficiency_metric_weighted", 0.0)
                ),
                efficiency_category_metric_coverage={
                    key.removeprefix("efficiency_metric_coverage_"): float(value)
                    for key, value in eff.coverage_details.items()
                    if key.startswith("efficiency_metric_coverage_")
                },
                economics_workloads_represented=int(
                    econ.coverage_details.get("economics_workloads_represented", 0)
                ),
                economics_workloads_total=len(config.weights.workload_weights),
                economics_workload_weighted=float(
                    econ.coverage_details.get("economics_workload_weighted", 0.0)
                ),
                independent_or_community_evidence_share=quality,
                source_organization_count=len(organizations),
            ),
            cohort_id=scored_fingerprint[:16],
            cohort_model_ids=cohort_model_ids,
            dataset_fingerprint=complete_fingerprint,
            scored_data_fingerprint=scored_fingerprint,
            data_as_of=data_as_of,
            release_window_start=config.eligibility.release_start,
            release_window_end=config.eligibility.release_end,
            engine_version=ENGINE_VERSION,
            normalization_version=NORMALIZATION_VERSION,
            config_fingerprint=config.fingerprint,
            formula_version=FORMULA_VERSION,
        )
        results.append(result)
    return results


def score_bundle(bundle: ScoringBundle, *, allow_unready: bool = False) -> list[ScoringResult]:
    """Score real evidence only after the bundle's governance checks have passed."""
    return score_dataset(bundle.dataset, bundle.config, allow_unready=allow_unready)
