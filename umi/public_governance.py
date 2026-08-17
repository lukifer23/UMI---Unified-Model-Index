"""v0.5 packaging that does not require new public evidence."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from umi.edition import load_public_edition_config
from umi.identity import load_public_identities
from umi.public import ROOT, public_series_specs
from umi.public_blockers import write_blocker_report
from umi.public_certificate import EPOCH_SHA256, verify_epoch_zip
from umi.public_sensitivity import write_weight_sensitivity
from umi.version import ENGINE_VERSION, PACKAGE_VERSION


def source_concentration(*, edition_name: str = "v0.5") -> dict[str, Any]:
    edition = load_public_edition_config(edition=edition_name)
    capability = edition.weights.capability_domains
    operational = edition.weights.operational_efficiency
    access = edition.weights.access_economics
    domain_weights = {
        "capability": {item.value: weight for item, weight in capability.items()},
        "operational_efficiency": {item.value: weight for item, weight in operational.items()},
        "access_economics": {item.value: weight for item, weight in access.items()},
    }
    component_orgs: dict[str, dict[str, float]] = {
        "capability": defaultdict(float),
        "operational_efficiency": defaultdict(float),
        "access_economics": defaultdict(float),
    }
    for family in edition.families:
        parent_weight = domain_weights[family.component][family.parent]
        share = family.weight * parent_weight
        component_orgs[family.component][family.source_organization] += share
    cap_applied = edition.eligibility.maximum_source_share
    components: dict[str, Any] = {}
    for component, shares in component_orgs.items():
        orgs = {org: round(share, 12) for org, share in sorted(shares.items())}
        apply_cap = len(orgs) >= 2
        components[component] = {
            "source_shares": orgs,
            "maximum_source_share": cap_applied if apply_cap else None,
            "cap_applied": apply_cap,
            "largest_share": max(orgs.values()) if orgs else 0.0,
        }
        if apply_cap and components[component]["largest_share"] - cap_applied > 1e-12:
            raise ValueError(f"{component} source share exceeds the configured cap")
    return {
        "edition_id": edition.edition_id,
        "components": components,
    }


def edition_manifest(*, edition_name: str = "v0.5") -> dict[str, Any]:
    edition = load_public_edition_config(edition=edition_name)
    identities = load_public_identities(edition=edition_name)
    return {
        "edition_id": edition.edition_id,
        "formula_version": edition.formula_version,
        "normalization_version": edition.normalization_version,
        "engine_version": ENGINE_VERSION,
        "package_version": PACKAGE_VERSION,
        "source_artifact_sha256": verify_epoch_zip(),
        "series": [spec["id"] for spec in public_series_specs(edition)],
        "entity_ids": [item.entity_id for item in identities],
        "required_common_core_coverage": edition.eligibility.required_common_core_coverage,
        "minimum_anchor_panel": edition.eligibility.minimum_anchor_panel,
        "maximum_source_share": edition.eligibility.maximum_source_share,
    }


def write_governance_artifacts(
    output_dir: Path | None = None,
    *,
    edition_name: str = "v0.5",
) -> dict[str, Any]:
    if edition_name != "v0.5":
        raise ValueError("governance artifacts are a v0.5 surface")
    destination = output_dir or ROOT / "data" / "editions" / "v0.5" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    blockers = write_blocker_report(destination)
    concentration = source_concentration(edition_name=edition_name)
    manifest = edition_manifest(edition_name=edition_name)
    if manifest["source_artifact_sha256"] != EPOCH_SHA256:
        raise ValueError("governance zip checksum does not match the registry")
    (destination / "source-concentration.json").write_text(
        json.dumps(concentration, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "edition-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    certificate_path = destination / "public-index-certificate.json"
    if certificate_path.is_file():
        certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
        pairwise = {
            "edition_id": certificate["edition_id"],
            "pairs": certificate["pairwise_indistinguishable"],
        }
        (destination / "pairwise-comparisons.json").write_text(
            json.dumps(pairwise, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    uncertainty_path = destination / "uncertainty.json"
    ablation = None
    stability = None
    if uncertainty_path.is_file():
        from umi.public_stability import write_rank_stability_artifacts

        scores = json.loads((destination / "model-scores.json").read_text(encoding="utf-8"))
        uncertainty = json.loads(uncertainty_path.read_text(encoding="utf-8"))
        pack = write_rank_stability_artifacts(
            destination, scores, uncertainty, edition_name=edition_name
        )
        ablation = pack["source_ablation"]
        stability = pack["rank_stability"]
    sensitivity = write_weight_sensitivity(destination, edition_name=edition_name)
    return {
        "blocker_report": blockers,
        "source_concentration": concentration,
        "edition_manifest": manifest,
        "source_ablation": ablation,
        "rank_stability": stability,
        "weight_sensitivity": sensitivity,
    }
