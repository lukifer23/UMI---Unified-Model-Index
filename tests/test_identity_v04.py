from __future__ import annotations

import pytest
from pydantic import ValidationError

from umi.edition import EntityKind
from umi.identity import (
    PublicSystemIdentity,
    evidence_matches_entity,
    identity_by_id,
    load_public_identities,
)


def test_five_pilot_identities_are_exact_and_kinded() -> None:
    entities = load_public_identities()
    by_id = {item.entity_id: item for item in entities}
    assert set(by_id) == {
        "claude-opus-5-max",
        "claude-fable-5-max",
        "gpt-5.6-sol-max",
        "kimi-k3-max",
        "glm-5.2-max",
    }
    assert by_id["claude-fable-5-max"].entity_kind == EntityKind.FALLBACK_COMPOSITE_SERVICE
    assert by_id["claude-fable-5-max"].fallback_targets == ("claude-opus-4.8",)
    assert by_id["claude-opus-5-max"].entity_kind == EntityKind.SINGLE_MODEL_SERVICE
    assert by_id["glm-5.2-max"].reasoning_mode == "xhigh"


def test_composite_and_pure_evidence_cannot_merge() -> None:
    fable = identity_by_id(load_public_identities(), "claude-fable-5-max")
    opus = identity_by_id(load_public_identities(), "claude-opus-5-max")
    ok, _ = evidence_matches_entity(
        entity=fable,
        source_effort="max",
        source_is_composite=True,
        source_fallbacks=("claude-opus-4.8",),
    )
    assert ok is True
    rejected, reason = evidence_matches_entity(
        entity=fable,
        source_effort="max",
        source_is_composite=False,
        source_fallbacks=(),
    )
    assert rejected is False
    assert "pure-model" in reason
    rejected, reason = evidence_matches_entity(
        entity=opus,
        source_effort="max",
        source_is_composite=True,
        source_fallbacks=("claude-opus-4.8",),
    )
    assert rejected is False
    assert "composite" in reason


def test_unknown_effort_cannot_map_to_max() -> None:
    opus = identity_by_id(load_public_identities(), "claude-opus-5-max")
    ok, reason = evidence_matches_entity(
        entity=opus,
        source_effort="unknown",
        source_is_composite=False,
        source_fallbacks=(),
    )
    assert ok is False
    assert "unknown effort" in reason


def test_single_model_identity_rejects_fallback_targets() -> None:
    with pytest.raises(ValidationError, match="not a composite"):
        PublicSystemIdentity(
            entity_id="broken",
            entity_kind=EntityKind.SINGLE_MODEL_SERVICE,
            developer="x",
            named_release="x",
            revision=None,
            release_date="2026-07-01",
            effort_setting="max",
            reasoning_mode="max",
            serving_provider=None,
            endpoint_id=None,
            service_tier=None,
            region=None,
            interface="public_api",
            harness=None,
            scaffold=None,
            primary_target="x",
            fallback_targets=("y",),
            route_scope="none",
            fallback_trigger="none",
            route_rate=None,
            route_rate_evidence=None,
            run_level_routes_available=False,
        )
