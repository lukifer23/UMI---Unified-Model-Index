"""Exact v0.4 deployable-system identity."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import Field, model_validator

from umi.edition import ConfigModel, EntityKind, edition_config_dir


class PublicSystemIdentity(ConfigModel):
    entity_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    entity_kind: EntityKind
    developer: str = Field(min_length=1)
    named_release: str = Field(min_length=1)
    revision: str | None = None
    release_date: date
    effort_setting: str = Field(min_length=1)
    reasoning_mode: str = Field(min_length=1)
    serving_provider: str | None = None
    endpoint_id: str | None = None
    service_tier: str | None = None
    region: str | None = None
    interface: str = Field(min_length=1)
    harness: str | None = None
    scaffold: str | None = None
    primary_target: str = Field(min_length=1)
    fallback_targets: tuple[str, ...] = ()
    route_scope: str = Field(min_length=1)
    fallback_trigger: str = Field(min_length=1)
    route_rate: float | None = Field(default=None, ge=0, le=1)
    route_rate_evidence: str | None = None
    run_level_routes_available: bool

    @model_validator(mode="after")
    def validate_kind_consistency(self) -> PublicSystemIdentity:
        if self.entity_kind == EntityKind.FALLBACK_COMPOSITE_SERVICE:
            if not self.fallback_targets:
                raise ValueError(f"{self.entity_id} composite service has no fallback targets")
        elif self.fallback_targets:
            raise ValueError(f"{self.entity_id} is not a composite service but lists fallbacks")
        if self.effort_setting.lower() == "unknown":
            raise ValueError(f"{self.entity_id} effort cannot be unknown")
        token = f"-{self.effort_setting}"
        if not self.entity_id.endswith(token):
            raise ValueError(f"{self.entity_id} must end with {token}")
        return self


def load_public_identities(
    path: Path | None = None,
    *,
    edition: str = "v0.4",
    bundle_dir: Path | str | None = None,
) -> tuple[PublicSystemIdentity, ...]:
    source = path or edition_config_dir(edition, bundle_dir=bundle_dir) / "identities.yaml"
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "entities" not in raw:
        raise ValueError(f"identity manifest missing entities: {source}")
    entities = tuple(PublicSystemIdentity.model_validate(item) for item in raw["entities"])
    ids = [item.entity_id for item in entities]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate public entity IDs")
    return entities


def identity_by_id(
    entities: tuple[PublicSystemIdentity, ...], entity_id: str
) -> PublicSystemIdentity:
    matches = [item for item in entities if item.entity_id == entity_id]
    if len(matches) != 1:
        raise ValueError(f"expected one identity for {entity_id}")
    return matches[0]


def evidence_matches_entity(
    *,
    entity: PublicSystemIdentity,
    source_effort: str | None,
    source_is_composite: bool,
    source_fallbacks: tuple[str, ...],
    reviewed_crosswalk_effort: str | None = None,
) -> tuple[bool, str]:
    if source_effort is None or source_effort.lower() in {"unknown", ""}:
        if (
            reviewed_crosswalk_effort
            and reviewed_crosswalk_effort.lower() == entity.effort_setting.lower()
        ):
            return True, "reviewed crosswalk effort; row effort field blank"
        return False, "unknown effort cannot map without a reviewed crosswalk"
    if source_effort.lower() != entity.effort_setting.lower():
        return False, "effort does not match the scored entity"
    if entity.entity_kind == EntityKind.FALLBACK_COMPOSITE_SERVICE:
        if source_is_composite:
            if not set(source_fallbacks).intersection(entity.fallback_targets):
                return False, "composite evidence fallbacks do not match the product"
            return True, "composite product match"
        return True, "exact product-label run of the composite service"
    if source_is_composite or source_fallbacks:
        return False, "composite evidence cannot score a single-model entity"
    return True, "single-model match"
