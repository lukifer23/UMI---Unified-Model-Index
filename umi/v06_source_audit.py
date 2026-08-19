"""Strict, offline v0.6 public-source audit.

v0.6 deliberately has no scoring adapter.  It verifies the provenance and rights
of the frozen public evidence already in this repository, reports the existing
headline gates, and abstains until public artifacts satisfy all scored-input
requirements.  It must never manufacture an Overall score from a source dossier.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import Field, model_validator

from umi.edition import ConfigModel
from umi.loading import SourceRegistry, load_source_registry

ROOT = Path(__file__).resolve().parents[1]
V06_EDITION_ID = "umi-public-v0.6"
V06_RELEASE_CLASS = "strict_public_source_audit"
V06_REPORT_VERSION = "umi-public-v0.6-source-audit-v1"
CURRENT_FIVE = (
    "claude-fable-5-max",
    "claude-opus-5-max",
    "gpt-5.6-sol-max",
    "kimi-k3-max",
    "glm-5.2-max",
)
_SCOPE_RANK = {"facts_only": 0, "full_artifact": 1}


class SourceRequirement(ConfigModel):
    requirement_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    component: str = Field(pattern=r"^[a-z_]+$")
    description: str = Field(min_length=1)
    source_artifact_ids: tuple[str, ...] = ()
    minimum_redistribution_scope: str = Field(pattern=r"^(facts_only|full_artifact)$")
    requires_exact_deployment: bool
    requires_attempt_residuals: bool


class SourceAuditConfig(ConfigModel):
    edition_id: str
    release_class: str
    evidence_snapshot_cutoff: str
    target_cohort: tuple[str, ...]
    baseline_artifacts: dict[str, str]
    source_requirements: tuple[SourceRequirement, ...]

    @model_validator(mode="after")
    def validate_contract(self) -> SourceAuditConfig:
        if self.edition_id != V06_EDITION_ID:
            raise ValueError(f"v0.6 audit edition must be {V06_EDITION_ID}")
        if self.release_class != V06_RELEASE_CLASS:
            raise ValueError(f"v0.6 release_class must be {V06_RELEASE_CLASS}")
        if self.evidence_snapshot_cutoff != "2026-08-19T00:00:00Z":
            raise ValueError("v0.6 evidence snapshot cutoff is fixed at 2026-08-19 UTC")
        if self.target_cohort != CURRENT_FIVE:
            raise ValueError("v0.6 target cohort must remain the five exact pilot configurations")
        ids = [item.requirement_id for item in self.source_requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("v0.6 source requirement IDs must be unique")
        required_baselines = {"publication_audit", "blocker_report", "source_registry"}
        if set(self.baseline_artifacts) != required_baselines:
            raise ValueError("v0.6 requires publication audit, blocker report, and source registry")
        return self


class GateAssessment(ConfigModel):
    observed: float = Field(ge=0)
    required: float = Field(ge=0)
    passes: bool
    unit: str


class SourceArtifactAssessment(ConfigModel):
    artifact_id: str
    artifact_path: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    actual_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    checksum_valid: bool
    license_id: str
    redistribution_scope: str
    source_url: str
    source_organization: str


class RequirementAssessment(ConfigModel):
    requirement_id: str
    component: str
    description: str
    source_artifact_ids: tuple[str, ...]
    minimum_redistribution_scope: str
    requires_exact_deployment: bool
    requires_attempt_residuals: bool
    passes: bool
    failures: tuple[str, ...]


class SourceAuditModel(ConfigModel):
    entity_id: str
    v05_governed_partial_score: float | None = None
    headline_overall: float | None = None
    headline_eligible: bool
    gates: dict[str, GateAssessment]
    blockers: tuple[str, ...]


class V06SourceAuditReport(ConfigModel):
    report_version: str
    edition_id: str
    release_class: str
    evidence_snapshot_cutoff: str
    publication_scope: str
    publication_state: str
    headline_eligible: bool
    headline_overall: float | None = None
    target_cohort: tuple[str, ...]
    gates: dict[str, GateAssessment]
    models: tuple[SourceAuditModel, ...]
    source_artifacts: tuple[SourceArtifactAssessment, ...]
    requirements: tuple[RequirementAssessment, ...]
    blockers: tuple[str, ...]
    unresolved_requirement_ids: tuple[str, ...]
    v05_scored_data_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_audit_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    narrative: tuple[str, ...]

    @model_validator(mode="after")
    def enforce_abstention(self) -> V06SourceAuditReport:
        if self.publication_scope != V06_RELEASE_CLASS:
            raise ValueError("v0.6 source audit must use its strict publication scope")
        if self.headline_eligible or self.headline_overall is not None:
            raise ValueError("v0.6 source audit must not manufacture a headline Overall")
        if not self.unresolved_requirement_ids:
            raise ValueError("a scoring release must replace the v0.6 abstention audit")
        if any(item.headline_eligible or item.headline_overall is not None for item in self.models):
            raise ValueError("v0.6 model rows must preserve headline abstention")
        return self


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one mapping")
    return cast(dict[str, Any], value)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return cast(dict[str, Any], value)


def load_v06_source_audit_config(root: Path = ROOT) -> SourceAuditConfig:
    path = root / "config" / "editions" / "v0.6" / "source-audit.yaml"
    return SourceAuditConfig.model_validate(_read_yaml(path))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_fingerprint(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _source_snapshot_map(registry: SourceRegistry) -> dict[str, Any]:
    return {item.id: item for item in registry.snapshots}


def _artifact_assessment(snapshot: Any, *, source_root: Path) -> SourceArtifactAssessment:
    artifact_path = source_root / snapshot.artifact_path
    actual_sha256 = _sha256(artifact_path) if artifact_path.is_file() else None
    source = snapshot.source
    return SourceArtifactAssessment(
        artifact_id=snapshot.id,
        artifact_path=(Path("data") / "sources" / snapshot.artifact_path).as_posix(),
        artifact_sha256=snapshot.artifact_sha256,
        actual_sha256=actual_sha256,
        checksum_valid=actual_sha256 == snapshot.artifact_sha256,
        license_id=snapshot.license_id,
        redistribution_scope=snapshot.redistribution_scope.value,
        source_url=str(source.url),
        source_organization=source.organization,
    )


def _requirement_assessment(
    requirement: SourceRequirement,
    artifacts: dict[str, SourceArtifactAssessment],
) -> RequirementAssessment:
    failures: list[str] = []
    if not requirement.source_artifact_ids:
        failures.append("no frozen public artifact is registered")
    for artifact_id in requirement.source_artifact_ids:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            failures.append(f"source artifact is not registered: {artifact_id}")
            continue
        if not artifact.checksum_valid:
            failures.append(f"artifact checksum is not verified: {artifact_id}")
        if _SCOPE_RANK[artifact.redistribution_scope] < _SCOPE_RANK[
            requirement.minimum_redistribution_scope
        ]:
            failures.append(
                f"{artifact_id} is {artifact.redistribution_scope}, requires "
                f"{requirement.minimum_redistribution_scope}"
            )
    if requirement.requires_exact_deployment:
        failures.append("no frozen exact-deployment evidence binding is available")
    if requirement.requires_attempt_residuals:
        failures.append("attempt-level residuals are not redistributable in the admitted evidence")
    return RequirementAssessment(
        requirement_id=requirement.requirement_id,
        component=requirement.component,
        description=requirement.description,
        source_artifact_ids=requirement.source_artifact_ids,
        minimum_redistribution_scope=requirement.minimum_redistribution_scope,
        requires_exact_deployment=requirement.requires_exact_deployment,
        requires_attempt_residuals=requirement.requires_attempt_residuals,
        passes=not failures,
        failures=tuple(failures),
    )


def _gate(value: dict[str, Any]) -> GateAssessment:
    return GateAssessment.model_validate(value)


def build_v06_source_audit(root: Path = ROOT) -> dict[str, Any]:
    config = load_v06_source_audit_config(root)
    baselines = {name: root / relative for name, relative in config.baseline_artifacts.items()}
    publication_audit = _read_json(baselines["publication_audit"])
    blocker_report = _read_json(baselines["blocker_report"])
    registry = load_source_registry(baselines["source_registry"])
    registry_map = _source_snapshot_map(registry)

    required_ids = tuple(
        sorted(
            {
                artifact_id
                for item in config.source_requirements
                for artifact_id in item.source_artifact_ids
            }
        )
    )
    missing_registry = [item for item in required_ids if item not in registry_map]
    if missing_registry:
        message = "v0.6 source requirements are missing registry entries: "
        raise ValueError(message + ", ".join(missing_registry))
    source_root = baselines["source_registry"].parent
    artifacts = {
        artifact_id: _artifact_assessment(registry_map[artifact_id], source_root=source_root)
        for artifact_id in required_ids
    }
    requirements = tuple(
        _requirement_assessment(item, artifacts) for item in config.source_requirements
    )
    audit_models = {str(item["entity_id"]): item for item in publication_audit["models"]}
    missing_models = [item for item in config.target_cohort if item not in audit_models]
    if missing_models:
        raise ValueError("v0.6 source audit is missing target models: " + ", ".join(missing_models))
    models = tuple(
        SourceAuditModel(
            entity_id=entity_id,
            v05_governed_partial_score=audit_models[entity_id].get("governed_score"),
            headline_overall=None,
            headline_eligible=False,
            gates={name: _gate(value) for name, value in audit_models[entity_id]["gates"].items()},
            blockers=tuple(str(item) for item in audit_models[entity_id]["blockers"]),
        )
        for entity_id in config.target_cohort
    )
    unresolved = tuple(item.requirement_id for item in requirements if not item.passes)
    reported_blockers = tuple(str(item["blocker_id"]) for item in blocker_report["blockers"])
    fingerprint_payload = {
        "config": config.model_dump(mode="json"),
        "publication_audit": publication_audit,
        "blocker_report": blocker_report,
        "source_artifacts": [artifacts[item].model_dump(mode="json") for item in sorted(artifacts)],
        "requirements": [item.model_dump(mode="json") for item in requirements],
    }
    report = {
        "report_version": V06_REPORT_VERSION,
        "edition_id": config.edition_id,
        "release_class": config.release_class,
        "evidence_snapshot_cutoff": config.evidence_snapshot_cutoff,
        "publication_scope": config.release_class,
        "publication_state": "verified_abstention",
        "headline_eligible": False,
        "headline_overall": None,
        "target_cohort": config.target_cohort,
        "gates": {
            name: _gate(value).model_dump(mode="json")
            for name, value in publication_audit["gates"].items()
        },
        "models": [item.model_dump(mode="json") for item in models],
        "source_artifacts": [artifacts[item].model_dump(mode="json") for item in sorted(artifacts)],
        "requirements": [item.model_dump(mode="json") for item in requirements],
        "blockers": reported_blockers,
        "unresolved_requirement_ids": unresolved,
        "v05_scored_data_fingerprint": publication_audit["scored_data_fingerprint"],
        "source_audit_fingerprint": _canonical_fingerprint(fingerprint_payload),
        "narrative": (
            "v0.6 verifies frozen public-source provenance and the existing headline "
            "gates; it does not score a new Overall.",
            "The Epoch archive is checksum-verified and redistributable, while the "
            "public DeepSWE and Artificial Analysis captures remain facts-and-citations only.",
            "The DeepSWE v1.1 public trial ledger was independently reconciled at its "
            "pinned checksum, but its raw redistribution scope is not established.",
            "No all-five provider-billing ledger, exact-deployment binding, or "
            "redistributable attempt residuals is admitted; headline Overall is withheld "
            "for every target.",
        ),
    }
    return V06SourceAuditReport.model_validate(report).model_dump(mode="json")


def render_v06_source_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# UMI Public v0.6 verified source audit",
        "",
        "v0.6 is a strict public-source audit for the five exact pilot configurations. "
        "It verifies what the frozen public evidence can support and withholds a "
        "headline Overall score.",
        "",
        f"- evidence cutoff: `{report['evidence_snapshot_cutoff']}`",
        f"- publication state: `{report['publication_state']}`",
        f"- headline eligible: `{str(report['headline_eligible']).lower()}`",
        f"- source-audit fingerprint: `{report['source_audit_fingerprint']}`",
        "",
        "## Existing headline gates",
        "",
        "| Gate | Observed | Required | Result |",
        "|---|---:|---:|---|",
    ]
    for name, gate in report["gates"].items():
        unit = gate["unit"]
        observed = f"{gate['observed']:.0f}" if unit == "domains" else f"{gate['observed']:.1%}"
        required = f"{gate['required']:.0f}" if unit == "domains" else f"{gate['required']:.1%}"
        result = "pass" if gate["passes"] else "**blocked**"
        lines.append(f"| `{name}` | {observed} | {required} | {result} |")
    lines.extend(
        [
            "",
            "## Frozen-source admissibility",
            "",
            "| Requirement | Sources | Result | Why |",
            "|---|---|---|---|",
        ]
    )
    for requirement in report["requirements"]:
        sources = ", ".join(f"`{item}`" for item in requirement["source_artifact_ids"]) or "none"
        why = "; ".join(requirement["failures"]) or "admitted"
        lines.append(
            f"| `{requirement['requirement_id']}` | {sources} | "
            f"{'pass' if requirement['passes'] else '**blocked**'} | {why} |"
        )
    lines.extend(["", "## Result", ""])
    lines.extend(f"- `{item}`" for item in report["unresolved_requirement_ids"])
    lines.extend(
        [
            "",
            "The audited v0.5 governed partial values remain provenance-bound historical inputs. "
            "They are not v0.6 Overall scores, and no missing requirement is imputed.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_v06_source_audit(
    output_dir: Path | None = None,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    report = build_v06_source_audit(root)
    destination = output_dir or root / "data" / "editions" / "v0.6" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "public-source-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if output_dir is None:
        docs = root / "docs" / "editions" / "v0.6" / "SOURCE_AUDIT.md"
        docs.parent.mkdir(parents=True, exist_ok=True)
        docs.write_text(render_v06_source_audit_markdown(report), encoding="utf-8")
    return report


def validate_v06_source_audit(root: Path = ROOT) -> dict[str, Any]:
    report = build_v06_source_audit(root)
    expected_path = root / "data" / "editions" / "v0.6" / "processed" / "public-source-audit.json"
    stored_matches = expected_path.is_file() and _read_json(expected_path) == report
    return {
        "valid": stored_matches,
        "edition": V06_EDITION_ID,
        "headline_eligible": False,
        "headline_overall": None,
        "publication_state": report["publication_state"],
        "unresolved_requirement_ids": report["unresolved_requirement_ids"],
        "source_audit_fingerprint": report["source_audit_fingerprint"],
    }
