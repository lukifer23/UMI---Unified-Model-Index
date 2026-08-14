from __future__ import annotations

from umi._component import weighted_available
from umi.capability import score_capability
from umi.config import OverallWeights, ProjectConfig
from umi.economics import score_economics
from umi.efficiency import score_efficiency
from umi.loading import Dataset
from umi.provenance import evidence_quality_share
from umi.schemas import Confidence, ScoringResult
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
        quality = evidence_quality_share(records_by_id.values())
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
        eligible = (
            overall is not None
            and overall_coverage >= config.eligibility.minimum_overall_coverage
            and len(domains) >= config.eligibility.minimum_capability_domains
        )
        diagnostics = sorted(
            {
                *cap.diagnostics,
                *eff.diagnostics,
                *econ.diagnostics,
                *([] if eligible else ["not eligible for headline Overall ranking"]),
            }
        )
        results.append(
            ScoringResult(
                model_id=model.id,
                capability=cap,
                efficiency=eff,
                economics=econ,
                overall=overall,
                value=value_score(cap.score, econ.score),
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
                config_fingerprint=config.fingerprint,
            )
        )
    return results
