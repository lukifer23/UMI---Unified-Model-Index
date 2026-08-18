"""Exact Public source-config crosswalks. No inferred effort or suffix rewriting."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field, model_validator

from umi.edition import ConfigModel, edition_config_dir
from umi.identity import PublicSystemIdentity


class PublicCrosswalkEntry(ConfigModel):
    source_config_id: str = Field(min_length=1)
    entity_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    source_effort: str = Field(min_length=1)
    status: str = Field(pattern=r"^exact$")

    @model_validator(mode="after")
    def require_explicit_effort_tokens(self) -> PublicCrosswalkEntry:
        if self.source_effort.lower() == "unknown":
            raise ValueError(f"{self.entity_id} source effort cannot be unknown")
        suffix = f"_{self.source_effort}"
        token = f"-{self.source_effort}"
        if not self.source_config_id.endswith(suffix):
            raise ValueError(
                f"{self.source_config_id} must end with {suffix} for effort {self.source_effort}"
            )
        if not self.entity_id.endswith(token):
            raise ValueError(f"{self.entity_id} must end with {token}")
        return self


class PublicSourceCrosswalk(ConfigModel):
    source_artifact_id: str = Field(min_length=1)
    entries: tuple[PublicCrosswalkEntry, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_exact_bindings(self) -> PublicSourceCrosswalk:
        configs = [item.source_config_id for item in self.entries]
        entities = [item.entity_id for item in self.entries]
        if len(configs) != len(set(configs)):
            raise ValueError("public crosswalk source_config_id values must be unique")
        if len(entities) != len(set(entities)):
            raise ValueError("public crosswalk entity_id values must be unique")
        return self


def load_public_crosswalk(
    *,
    edition: str = "v0.4",
    bundle_dir: Path | str | None = None,
) -> PublicSourceCrosswalk:
    path = edition_config_dir(edition, bundle_dir=bundle_dir) / "crosswalk.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"public crosswalk missing mapping: {path}")
    return PublicSourceCrosswalk.model_validate(raw)


def validate_public_crosswalk(
    crosswalk: PublicSourceCrosswalk,
    identities: tuple[PublicSystemIdentity, ...],
) -> None:
    by_id = {item.entity_id: item for item in identities}
    mapped = {item.entity_id: item for item in crosswalk.entries}
    missing = sorted(set(by_id) - set(mapped))
    if missing:
        raise ValueError("identities lack exact source crosswalks: " + ", ".join(missing))
    for entity_id, entry in mapped.items():
        identity = by_id.get(entity_id)
        if identity is None:
            continue
        if entry.source_effort.lower() != identity.effort_setting.lower():
            raise ValueError(
                f"{entity_id} crosswalk effort {entry.source_effort} "
                f"does not match identity {identity.effort_setting}"
            )


def entity_map_from_crosswalk(
    identities: tuple[PublicSystemIdentity, ...],
    *,
    edition: str,
    bundle_dir: Path | str | None = None,
) -> dict[str, str]:
    crosswalk = load_public_crosswalk(edition=edition, bundle_dir=bundle_dir)
    validate_public_crosswalk(crosswalk, identities)
    allowed = {item.entity_id for item in identities}
    return {
        item.source_config_id: item.entity_id
        for item in crosswalk.entries
        if item.entity_id in allowed
    }


def config_id_for_entity(entity_id: str, *, edition: str) -> str:
    crosswalk = load_public_crosswalk(edition=edition)
    matches = [item for item in crosswalk.entries if item.entity_id == entity_id]
    if len(matches) != 1:
        raise ValueError(f"expected one exact source config for {entity_id}")
    return matches[0].source_config_id
