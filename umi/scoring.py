from __future__ import annotations

import hashlib

from umi._component import weighted_available
from umi.capability import score_capability
from umi.config import OverallWeights, ProjectConfig
from umi.economics import score_economics
from umi.efficiency import score_efficiency
from umi.loading import Dataset
from umi.provenance import evidence_quality_share
from umi.schemas import Confidence, CoverageSummary, Domain, ScoringResult
from umi.validation import validate_dataset
from umi.value import value_score


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


def score_dataset(dataset: Dataset, config: ProjectConfig) -> list[ScoringResult]:
    validate_dataset(dataset, config).raise_for_errors()
    capability = score_capability(dataset, config)
    efficiency = score_efficiency(dataset, config)
    economics = score_economics(dataset, config)
    weights = config.weights.overall
    results: list[ScoringResult] = []
    cohort_model_ids = tuple(sorted(model.id for model in dataset.models))
    cohort_id = hashlib.sha256(
        (config.fingerprint + "\0" + "\0".join(cohort_model_ids)).encode()
    ).hexdigest()[:16]
    observed_dates = [
        item.evaluation_date for item in dataset.benchmarks if item.evaluation_date is not None
    ]
    observed_dates.extend(
        item.evaluation_date for item in dataset.efficiency if item.evaluation_date is not None
    )
    observed_dates.extend(item.evaluation_date for item in dataset.task_economics)
    observed_dates.extend(item.evaluation_date for item in dataset.external_indexes)
    evaluation_date = max(observed_dates) if observed_dates else config.eligibility.release_end
    for model in sorted(dataset.models, key=lambda item: item.id):
        cap = capability.components[model.id]
        eff = efficiency.components[model.id]
        econ = economics.components[model.id]
        component_values = {
            "capability": cap.score,
            "efficiency": eff.score,
            "economics": econ.score,
        }
        component_weights = {
            "capability": weights.capability,
            "efficiency": weights.efficiency,
            "economics": weights.economics,
        }
        overall, _ = weighted_available(component_values, component_weights)
        overall_coverage = (
            weights.capability * cap.coverage
            + weights.efficiency * eff.coverage
            + weights.economics * econ.coverage
        )
        records_by_id = {}
        for record in (
            *capability.evidence.get(model.id, ()),
            *efficiency.evidence.get(model.id, ()),
            *economics.evidence.get(model.id, ()),
        ):
            records_by_id[record.record_id] = record
        component_quality = {
            "capability": evidence_quality_share(capability.evidence.get(model.id, ())),
            "efficiency": evidence_quality_share(efficiency.evidence.get(model.id, ())),
            "economics": evidence_quality_share(economics.evidence.get(model.id, ())),
        }
        quality_denominator = overall_coverage
        quality_numerator = (
            weights.capability * cap.coverage * component_quality["capability"]
            + weights.efficiency * eff.coverage * component_quality["efficiency"]
            + weights.economics * econ.coverage * component_quality["economics"]
        )
        quality = quality_numerator / quality_denominator if quality_denominator else 0.0
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
        domains = capability.domains.get(model.id, ())
        efficiency_workload_coverage = float(
            eff.coverage_details.get("efficiency_workload_weighted", 0.0)
        )
        eligible = (
            overall is not None
            and overall_coverage >= config.eligibility.minimum_overall_coverage
            and len(domains) >= config.eligibility.minimum_capability_domains
            and config.eligibility.release_start
            <= model.release_date
            <= config.eligibility.release_end
            and (
                eff.score is None
                or efficiency_workload_coverage
                >= config.eligibility.minimum_efficiency_workload_coverage
            )
        )
        organizations = {record.source.organization for record in records_by_id.values()}
        confidence_reasons = [
            f"{overall_coverage:.0%} weighted coverage",
            f"{len(domains)}/{len(Domain)} capability domains represented",
            (
                f"{int(eff.coverage_details.get('efficiency_workloads_represented', 0))}/"
                f"{len(config.weights.workload_weights)} efficiency workload classes"
            ),
            f"{len(organizations)} source organizations",
            f"{quality:.0%} independent/community evidence",
        ]
        if len(organizations) < 2 and confidence == Confidence.HIGH:
            confidence = Confidence.MEDIUM
            confidence_reasons.append("confidence capped at Medium: single-source dependence")
        if len(domains) < config.eligibility.minimum_capability_domains:
            confidence = Confidence.LOW
            confidence_reasons.append("confidence capped at Low: insufficient capability breadth")
        diagnostics = sorted(
            {
                *cap.diagnostics,
                *eff.diagnostics,
                *econ.diagnostics,
                *([] if eligible else ["not eligible for headline Overall ranking"]),
                *(
                    []
                    if config.eligibility.release_start
                    <= model.release_date
                    <= config.eligibility.release_end
                    else ["model release date is outside the configured eligibility window"]
                ),
            }
        )
        results.append(
            ScoringResult(
                model_id=model.id,
                capability=cap,
                efficiency=eff,
                economics=econ,
                partial_overall_estimate=overall,
                headline_overall=overall if eligible else None,
                value=value_score(cap.score, econ.score, config.value.baseline, config.value.alpha),
                value_methodology=config.value.baseline,
                overall_coverage=overall_coverage,
                confidence=confidence,
                eligible=eligible,
                provisional=(
                    not eligible or cap.provisional or eff.provisional or econ.provisional
                ),
                capability_domains=domains,
                evidence_quality_share=quality,
                source_record_ids=tuple(sorted(records_by_id)),
                diagnostics=tuple(diagnostics),
                confidence_reasons=tuple(confidence_reasons),
                coverage=CoverageSummary(
                    overall_weighted=overall_coverage,
                    capability_domains_represented=len(domains),
                    capability_domains_total=len(Domain),
                    capability_family_weighted=float(
                        cap.coverage_details.get("capability_family_weighted", 0.0)
                    ),
                    efficiency_workloads_represented=int(
                        eff.coverage_details.get("efficiency_workloads_represented", 0)
                    ),
                    efficiency_workloads_total=len(config.weights.workload_weights),
                    efficiency_workload_weighted=efficiency_workload_coverage,
                    economics_workloads_represented=int(
                        econ.coverage_details.get("economics_workloads_represented", 0)
                    ),
                    economics_workloads_total=len(config.weights.workload_weights),
                    economics_workload_weighted=float(
                        econ.coverage_details.get("economics_workload_weighted", 0.0)
                    ),
                    independent_evidence_share=quality,
                    source_organization_count=len(organizations),
                ),
                cohort_id=cohort_id,
                cohort_model_ids=cohort_model_ids,
                evaluation_date=evaluation_date,
                normalization_version="umi-normalization-v0.2",
                config_fingerprint=config.fingerprint,
                formula_version="umi-methodology-v0.2-draft",
            )
        )
    return results
