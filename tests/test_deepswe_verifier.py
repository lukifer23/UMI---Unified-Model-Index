from __future__ import annotations

import hashlib
import json

import pytest

from scripts.verify_deepswe_trial_ledger import verify_trial_ledger


def _ledger_fixture() -> tuple[bytes, dict[str, object]]:
    rows = [
        {
            "config": "model-max",
            "included_in_score": True,
            "passed": True,
            "provider": "provider",
            "cost_usd": 2.0,
            "n_input_tokens": 10,
            "n_output_tokens": 3,
            "n_cache_tokens": 5,
            "agent_duration_seconds": 7,
            "n_agent_steps": 2,
        },
        {
            "config": "model-max",
            "included_in_score": True,
            "passed": False,
            "provider": "provider",
            "cost_usd": None,
            "n_input_tokens": 14,
            "n_output_tokens": 5,
            "n_cache_tokens": 9,
            "agent_duration_seconds": 11,
            "n_agent_steps": 4,
        },
        {
            "config": "model-max",
            "included_in_score": False,
            "passed": False,
            "provider": "provider",
            "cost_usd": None,
            "n_input_tokens": None,
            "n_output_tokens": None,
            "n_cache_tokens": None,
            "agent_duration_seconds": None,
            "n_agent_steps": None,
        },
    ]
    payload = json.dumps({"n_trials": 3, "rows": rows}, separators=(",", ":")).encode()
    facts: dict[str, object] = {
        "upstream_trial_ledger": {
            "url": "https://example.invalid/trials.json",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "declared_trial_count": 3,
            "selected_configuration_rows": 3,
            "included_scored_rows": 2,
        },
        "rows": [
            {
                "source_config_id": "model-max",
                "attempted_tasks": 2,
                "passed_attempts": 1,
                "pass_rate": 0.5,
                "serving_provider": "provider",
                "resource_observation_count": 2,
                "cost_observation_count": 1,
                "mean_cost_usd": 2.0,
                "mean_input_tokens": 12.0,
                "mean_output_tokens": 4.0,
                "mean_cached_tokens": 7.0,
                "mean_duration_seconds": 9.0,
                "mean_agent_steps": 3.0,
            }
        ],
    }
    return payload, facts


def test_deepswe_trial_ledger_verifier_preserves_incomplete_metric_count() -> None:
    payload, facts = _ledger_fixture()
    report = verify_trial_ledger(payload, facts)
    assert report["status"] == "verified"
    assert report["included_scored_rows"] == 2
    assert report["excluded_error_rows"] == 1
    row = report["rows"][0]
    assert row["observation_counts"]["mean_cost_usd"] == 1
    assert row["observation_counts"]["mean_input_tokens"] == 2


def test_deepswe_trial_ledger_verifier_fails_closed_on_checksum_drift() -> None:
    payload, facts = _ledger_fixture()
    with pytest.raises(ValueError, match="checksum changed"):
        verify_trial_ledger(payload + b" ", facts)


def test_deepswe_trial_ledger_verifier_fails_closed_on_partial_resource_metric() -> None:
    payload, facts = _ledger_fixture()
    ledger = json.loads(payload)
    ledger["rows"][1]["n_cache_tokens"] = None
    changed_payload = json.dumps(ledger, separators=(",", ":")).encode()
    facts["upstream_trial_ledger"]["sha256"] = hashlib.sha256(changed_payload).hexdigest()
    facts["rows"][0]["mean_cached_tokens"] = 5.0
    with pytest.raises(ValueError, match="resource denominator changed"):
        verify_trial_ledger(changed_payload, facts)
