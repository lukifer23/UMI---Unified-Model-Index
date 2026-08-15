from __future__ import annotations

import hashlib
import json

from analysis.compare import common_capability_comparison
from umi.bundle import ScoringBundle
from umi.fingerprints import scored_data_fingerprint
from umi.readiness import scoring_dataset
from umi.schemas import (
    CapabilityComparisonResult,
    CertificateStatus,
    ComparisonCertificate,
    ComparisonStatus,
)
from umi.scoring import score_bundle

CERTIFICATE_VERSION = "umi-certificate-v0.1"


def _fingerprint(payload: dict[str, object]) -> str:
    rendered = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(rendered.encode()).hexdigest()


def build_comparison_certificate(
    bundle: ScoringBundle, model_ids: tuple[str, ...]
) -> ComparisonCertificate:
    """Bind one governed common-evidence comparison to its exact source context."""
    score_bundle(bundle)
    comparison = CapabilityComparisonResult.model_validate(
        common_capability_comparison(bundle.dataset, bundle.config, model_ids)
    )
    models = {item.id: item for item in bundle.dataset.models}
    identity_assurance = {
        model_id: models[model_id].identity_assurance
        for model_id in comparison.comparison_model_ids
    }
    accepted_dataset, _ = scoring_dataset(bundle.dataset)
    scored_input = scored_data_fingerprint(accepted_dataset, bundle.config)

    if comparison.status == ComparisonStatus.INSUFFICIENT_COMMON_SUPPORT:
        abstention_reasons = (
            "no common ready capability benchmark series",
            *tuple(f"incompatible series: {item}" for item in comparison.incompatible_series),
        )
        payload: dict[str, object] = {
            "certificate_version": CERTIFICATE_VERSION,
            "status": CertificateStatus.INSUFFICIENT_COMMON_SUPPORT.value,
            "publication_label": comparison.publication_label,
            "comparison_group_id": comparison.comparison_group_id,
            "bundle_fingerprint": bundle.acceptance_manifest.fingerprint,
            "scored_input_fingerprint": scored_input,
            "evidence_profile_id": None,
            "normalization_panel_ids": (),
            "score_scale_id": None,
            "comparison_model_ids": comparison.comparison_model_ids,
            "common_benchmark_series": (),
            "raw_contributions": {},
            "normalized_contributions": {},
            "component_scores": {},
            "central_estimate_ranks": {},
            "rank_robustness": {},
            "coverage": {},
            "identity_assurance": identity_assurance,
            "source_record_ids": (),
            "source_artifact_ids": (),
            "source_artifact_checksums": {},
            "applied_normalization": (),
            "comparability_basis": (),
            "warnings": bundle.warnings,
            "abstention_reasons": abstention_reasons,
            "missing_evidence": comparison.missing_support_by_model,
        }
    else:
        score_scale = comparison.score_scale
        if score_scale is None or comparison.common_evidence_profile_id is None:
            raise ValueError("comparison certificate requires a common profile and score scale")
        raw_contributions = {
            item.model_id: item.primary_raw_results for item in comparison.scores
        }
        normalized_contributions = {
            item.model_id: item.contributions for item in comparison.scores
        }
        source_record_ids = tuple(
            sorted(
                {
                    record_id
                    for item in comparison.scores
                    for contribution in item.contributions
                    for record_id in contribution.source_record_ids
                }
            )
        )
        records = {item.record_id: item for item in bundle.dataset.benchmarks}
        source_artifact_ids = tuple(
            sorted(
                {
                    artifact_id
                    for record_id in source_record_ids
                    if (record := records.get(record_id)) is not None
                    if (artifact_id := record.source_artifact_id) is not None
                }
            )
        )
        snapshots = {item.id: item for item in bundle.source_registry.snapshots}
        checksums = {
            artifact_id: snapshots[artifact_id].artifact_sha256
            for artifact_id in source_artifact_ids
        }
        provisional = any(item.provisional for item in comparison.scores)
        payload = {
            "certificate_version": CERTIFICATE_VERSION,
            "status": (
                CertificateStatus.PROVISIONAL_COMPARISON.value
                if provisional
                else CertificateStatus.VALID_COMPARISON.value
            ),
            "publication_label": comparison.publication_label,
            "comparison_group_id": comparison.comparison_group_id,
            "bundle_fingerprint": bundle.acceptance_manifest.fingerprint,
            "scored_input_fingerprint": scored_input,
            "evidence_profile_id": comparison.common_evidence_profile_id,
            "normalization_panel_ids": score_scale.normalization_panel_ids,
            "score_scale_id": score_scale.id,
            "comparison_model_ids": comparison.comparison_model_ids,
            "common_benchmark_series": comparison.common_benchmark_series,
            "raw_contributions": raw_contributions,
            "normalized_contributions": normalized_contributions,
            "component_scores": {
                item.model_id: item.normalized_composite_score
                for item in comparison.scores
            },
            "central_estimate_ranks": {
                item.model_id: item.rank for item in comparison.scores
            },
            "rank_robustness": {
                item.model_id: item.rank_robustness
                for item in comparison.scores
                if item.rank_robustness is not None
            },
            "coverage": {item.model_id: item.coverage for item in comparison.scores},
            "identity_assurance": identity_assurance,
            "source_record_ids": source_record_ids,
            "source_artifact_ids": source_artifact_ids,
            "source_artifact_checksums": checksums,
            "applied_normalization": comparison.normalization_panels,
            "comparability_basis": (
                "same canonical ready benchmark series and compatibility cohorts",
                "same evidence-profile ID",
                "same bundle-wide stable normalization panels",
                "same score-scale, formula, normalization, and configuration identity",
                "exact model, release, effort, and source crosswalks validated by bundle",
            ),
            "warnings": bundle.warnings,
            "abstention_reasons": (),
            "missing_evidence": comparison.missing_support_by_model,
        }

    result_fingerprint = _fingerprint(
        json.loads(json.dumps(payload, default=lambda value: value.model_dump(mode="json")))
    )
    return ComparisonCertificate.model_validate(
        {**payload, "result_fingerprint": result_fingerprint}
    )
