from __future__ import annotations

import json
from pathlib import Path

import pytest

from umi.edition import SOURCE_CONCENTRATION_FAILED, load_public_edition_config
from umi.identity import PublicSystemIdentity, evidence_matches_entity, load_public_identities
from umi.public import _source_effort, score_public_edition
from umi.public_eligibility import decide_public_eligibility
from umi.public_governance import source_concentration


def test_suffix_is_not_effort_proof() -> None:
    row = {"Reasoning effort": "", "Name": "Grok 4.5", "Notes": ""}
    assert _source_effort(row, "grok-4.5_high") is None
    assert _source_effort(row, "grok-4.5_max") is None
    assert _source_effort(row, "gemini-3.1-pro-preview_xhigh") is None
    opus = next(
        item
        for item in load_public_identities(edition="v0.4")
        if item.entity_id == "claude-opus-5-max"
    )
    rejected, reason = evidence_matches_entity(
        entity=opus,
        source_effort=None,
        source_is_composite=False,
        source_fallbacks=(),
    )
    assert rejected is False
    assert "reviewed crosswalk" in reason


def test_blank_row_effort_accepted_only_with_reviewed_crosswalk() -> None:
    opus = next(
        item
        for item in load_public_identities(edition="v0.4")
        if item.entity_id == "claude-opus-5-max"
    )
    ok, reason = evidence_matches_entity(
        entity=opus,
        source_effort=None,
        source_is_composite=False,
        source_fallbacks=(),
        reviewed_crosswalk_effort="max",
    )
    assert ok is True
    assert "reviewed crosswalk" in reason


def test_source_cap_has_no_single_source_exemption() -> None:
    report = source_concentration(edition_name="v0.5")
    access = report["components"]["access_economics"]
    opeff = report["components"]["operational_efficiency"]
    assert access["cap_applied"] is True
    assert opeff["cap_applied"] is True
    assert access["largest_share"] == 1.0
    assert opeff["largest_share"] == 1.0
    assert access["exceeds_cap"] is True
    assert opeff["exceeds_cap"] is True
    assert report["certified_headline_allowed"] is False
    critpt_origin = load_public_edition_config(edition="v0.5")
    critpt = next(item for item in critpt_origin.families if item.id == "epoch-critpt")
    assert critpt.concentration_origin() == "artificial-analysis"
    assert critpt.data_distributor == "epoch"


def test_v05_eligibility_withholds_certified_headline() -> None:
    edition = load_public_edition_config(edition="v0.5")
    decision = decide_public_eligibility(edition)
    assert decision.certified is False
    assert decision.eligible is False
    assert SOURCE_CONCENTRATION_FAILED in decision.reason_codes
    assert "construct_incomplete" in decision.reason_codes
    payload = score_public_edition(edition_name="v0.5")
    assert payload["certified"] is False
    assert payload["publication_state"] == "provisional_public_score"


def test_v04_release_status_companion_does_not_mutate_scores() -> None:
    root = Path(__file__).resolve().parents[1]
    status = json.loads(
        (root / "data/editions/v0.4/processed/release-status.json").read_text(encoding="utf-8")
    )
    scores = json.loads(
        (root / "data/editions/v0.4/processed/model-scores.json").read_text(encoding="utf-8")
    )
    assert status["publication_state"] == "experimental_point_score"
    assert status["scored_data_fingerprint"] == scores["scored_data_fingerprint"]
    assert scores["publication_state"] == "published"


def test_identity_schema_still_rejects_unknown_effort_entities() -> None:
    payload = load_public_identities(edition="v0.4")[0].model_dump(mode="json")
    payload["effort_setting"] = "unknown"
    with pytest.raises(Exception, match="unknown"):
        PublicSystemIdentity.model_validate(payload)
