from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from umi.attempt_ledger import aggregate_attempt_ledger, attempt_ledger_fingerprint
from umi.cli import build_parser, run
from umi.readiness import readiness_failures
from umi.schemas import AttemptLedger, BillingEvidenceKind, ModelConfiguration


def _ledger_payload() -> dict[str, object]:
    return {
        "ledger_id": "controlled-coding-cohort-1",
        "source": {
            "organization": "Independent Evaluation Lab",
            "url": "https://example.org/evaluation",
            "accessed": "2026-08-15",
        },
        "source_artifact_id": "controlled-coding-cohort-1-raw",
        "source_artifact_sha256": "1" * 64,
        "crosswalk_entry_id": "controlled-model-max",
        "capture_type": "raw_upstream_payload",
        "redistribution_scope": "full_artifact",
        "model_release_date": "2026-07-01",
        "measurement_as_of_date": "2026-08-15",
        "deployment": {
            "id": "controlled-model-max-provider-standard",
            "model_id": "controlled-model-max",
            "configuration": "max",
            "named_release": "Controlled Model",
            "source_model_id": "provider/controlled-model-20260701",
            "serving_provider": "provider",
            "endpoint_id": "provider/controlled-model-20260701",
            "service_tier": "standard",
            "provider_snapshot_id": "controlled-model-20260701",
            "region": "us",
            "configuration_verification": {
                "model_label_exact": True,
                "release_label_exact": True,
                "effort_label_exact": True,
                "fallback_absent": True,
                "provider_snapshot_verified": True,
                "endpoint_verified": True,
                "service_tier_verified": True,
                "deployment_identity_verified": True,
            },
        },
        "workload": "controlled-coding",
        "workload_category": "coding_agents",
        "interaction_profile": "autonomous_task",
        "operational_profile_id": "controlled-coding-harness-1-autonomous",
        "cohort_key": "controlled-coding-v1",
        "evaluation_date": "2026-08-15",
        "workload_version": "controlled-coding-v1",
        "harness_version": "harness-1.0",
        "harness_owner": "Independent Evaluation Lab",
        "run_executor": "Independent Evaluation Lab",
        "evaluator": "Independent Evaluation Lab",
        "success_definition_id": "repository-tests-pass-v1",
        "success_definition": "Repository tests pass without prohibited changes",
        "tools_enabled": True,
        "signal_id": "controlled-coding-resources",
        "record_status": "ready",
        "scoring_disposition": "scored",
        "attempts": [
            {
                "task_id": "task-a",
                "attempt_id": "attempt-a",
                "success": True,
                "input_tokens": 100,
                "output_tokens": 20,
                "reasoning_tokens": 10,
                "cache_read_tokens": 30,
                "cache_write_tokens": 5,
                "turns": 2,
                "agent_steps": 4,
                "wall_seconds": 40,
                "tool_calls": 3,
                "retry_count": 0,
                "observed_cost_usd": 1.0,
                "billing_evidence": "provider_billing_record",
                "cost_evidence_id": "bill-row-a",
                "provider_request_id": "request-a",
                "generation_id": "generation-a",
                "resolved_model_id": "provider/controlled-model-20260701",
                "serving_provider": "provider",
                "service_tier": "standard",
                "data_region": "us",
                "upstream_id": "upstream-a",
            },
            {
                "task_id": "task-b",
                "attempt_id": "attempt-b",
                "success": False,
                "input_tokens": 200,
                "output_tokens": 40,
                "reasoning_tokens": 20,
                "cache_read_tokens": 60,
                "cache_write_tokens": 10,
                "turns": 4,
                "agent_steps": 8,
                "wall_seconds": 80,
                "tool_calls": 6,
                "retry_count": 1,
                "observed_cost_usd": 2.0,
                "billing_evidence": "provider_billing_record",
                "cost_evidence_id": "bill-row-b",
                "provider_request_id": "request-b",
                "generation_id": "generation-b",
                "resolved_model_id": "provider/controlled-model-20260701",
                "serving_provider": "provider",
                "service_tier": "standard",
                "data_region": "us",
                "upstream_id": "upstream-b",
                "error_kind": "task_failed",
            },
            {
                "task_id": "task-c",
                "attempt_id": "attempt-c",
                "success": True,
                "input_tokens": 300,
                "output_tokens": 60,
                "reasoning_tokens": 30,
                "cache_read_tokens": 90,
                "cache_write_tokens": 15,
                "turns": 6,
                "agent_steps": 12,
                "wall_seconds": 120,
                "tool_calls": 9,
                "retry_count": 2,
                "observed_cost_usd": 3.0,
                "billing_evidence": "provider_billing_record",
                "cost_evidence_id": "bill-row-c",
                "provider_request_id": "request-c",
                "generation_id": "generation-c",
                "resolved_model_id": "provider/controlled-model-20260701",
                "serving_provider": "provider",
                "service_tier": "standard",
                "data_region": "us",
                "upstream_id": "upstream-c",
            },
        ],
    }


def _model() -> ModelConfiguration:
    return ModelConfiguration.model_validate(
        {
            "id": "controlled-model-max",
            "family": "Controlled Model",
            "provider": "Developer",
            "release_date": "2026-07-01",
            "configuration": "max",
            "identity_kind": "immutable_provider_snapshot",
            "identity_assurance": "verified",
            "named_release": "Controlled Model",
            "provider_snapshot_id": "controlled-model-20260701",
            "api_model_id": "provider/controlled-model-20260701",
            "serving_provider": "provider",
            "endpoint_id": "provider/controlled-model-20260701",
            "service_tier": "standard",
            "region": "us",
            "open_weights": False,
        }
    )


def test_attempt_ledger_aggregates_complete_resources_and_observed_economics() -> None:
    result = aggregate_attempt_ledger(AttemptLedger.model_validate(_ledger_payload()))
    assert result.attempt_count == 3
    assert result.task_count == 3
    assert result.successful_attempts == 2
    assert result.success_rate == pytest.approx(2 / 3)
    assert len(result.efficiency_records) == 1
    resources = result.efficiency_records[0]
    assert resources.mean_input_tokens == 200
    assert resources.mean_cached_tokens == 60
    assert resources.mean_turns == 4
    assert resources.interaction_profile is not None
    assert resources.interaction_profile.value == "autonomous_task"
    assert resources.operational_profile_id == "controlled-coding-harness-1-autonomous"
    assert resources.success_definition_id == "repository-tests-pass-v1"
    assert resources.observation_counts is not None
    assert resources.observation_counts.input_tokens == 3
    assert resources.record_status.value == "ready"
    assert readiness_failures(resources, _model()) == ()
    assert len(result.economics_records) == 1
    economics = result.economics_records[0]
    assert economics.total_observed_cost_usd == 6
    assert economics.mean_cost_usd == 3
    assert economics.cost_observation_count == 3
    assert economics.interaction_profile is not None
    assert economics.interaction_profile.value == "autonomous_task"
    assert economics.operational_profile_id == "controlled-coding-harness-1-autonomous"
    assert economics.success_definition_id == "repository-tests-pass-v1"
    assert readiness_failures(economics, _model()) == ()
    assert any("cache-write tokens retained" in item for item in result.diagnostics)


def test_attempt_ledger_fingerprint_and_aggregation_are_order_invariant() -> None:
    payload = _ledger_payload()
    reversed_payload = deepcopy(payload)
    reversed_payload["attempts"] = list(reversed(reversed_payload["attempts"]))
    first = AttemptLedger.model_validate(payload)
    second = AttemptLedger.model_validate(reversed_payload)
    assert attempt_ledger_fingerprint(first) == attempt_ledger_fingerprint(second)
    assert aggregate_attempt_ledger(first) == aggregate_attempt_ledger(second)

    interactive_payload = deepcopy(payload)
    interactive_payload["interaction_profile"] = "interactive_round"
    interactive = AttemptLedger.model_validate(interactive_payload)
    assert attempt_ledger_fingerprint(first) != attempt_ledger_fingerprint(interactive)

    profile_payload = deepcopy(payload)
    profile_payload["operational_profile_id"] = "controlled-coding-harness-2-autonomous"
    profile = AttemptLedger.model_validate(profile_payload)
    assert attempt_ledger_fingerprint(first) != attempt_ledger_fingerprint(profile)

    success_payload = deepcopy(payload)
    success_payload["success_definition_id"] = "repository-tests-pass-v2"
    success = AttemptLedger.model_validate(success_payload)
    assert attempt_ledger_fingerprint(first) != attempt_ledger_fingerprint(success)


def test_partial_metric_is_split_from_ready_complete_resources() -> None:
    payload = _ledger_payload()
    payload["attempts"][1]["tool_calls"] = None
    result = aggregate_attempt_ledger(AttemptLedger.model_validate(payload))
    assert len(result.efficiency_records) == 2
    ready = next(item for item in result.efficiency_records if item.record_status.value == "ready")
    diagnostic = next(
        item for item in result.efficiency_records if item.record_status.value == "diagnostic_only"
    )
    assert ready.mean_input_tokens == 200
    assert ready.mean_tool_calls is None
    assert diagnostic.mean_tool_calls == 6
    assert diagnostic.observation_counts is not None
    assert diagnostic.observation_counts.tool_calls == 2
    assert readiness_failures(ready, _model()) == ()
    assert len(result.economics_records) == 1


def test_non_billing_cost_and_zero_success_never_emit_observed_economics() -> None:
    router_payload = _ledger_payload()
    for attempt in router_payload["attempts"]:
        attempt["billing_evidence"] = "router_response_cost"
    router_result = aggregate_attempt_ledger(AttemptLedger.model_validate(router_payload))
    assert router_result.economics_records == ()
    assert "cost evidence is not provider-billing-record complete" in router_result.diagnostics

    zero_payload = _ledger_payload()
    for attempt in zero_payload["attempts"]:
        attempt["success"] = False
    zero_result = aggregate_attempt_ledger(AttemptLedger.model_validate(zero_payload))
    assert zero_result.success_rate == 0
    assert zero_result.economics_records == ()
    assert any("zero successes" in item for item in zero_result.diagnostics)


def test_economics_readiness_rejects_incomplete_or_non_billing_cost() -> None:
    result = aggregate_attempt_ledger(AttemptLedger.model_validate(_ledger_payload()))
    economics = result.economics_records[0]
    incomplete = economics.model_copy(update={"cost_observation_count": 2})
    assert "economics cost observations do not cover every attempt" in readiness_failures(
        incomplete, _model()
    )
    router_cost = economics.model_copy(
        update={"billing_evidence": BillingEvidenceKind.ROUTER_RESPONSE_COST}
    )
    assert "provider billing-record evidence is missing" in readiness_failures(
        router_cost, _model()
    )

    inconsistent = economics.model_dump(mode="python")
    inconsistent["mean_cost_usd"] = 2.5
    with pytest.raises(ValidationError, match="does not reconcile"):
        type(economics).model_validate(inconsistent)


def test_attempt_ledger_rejects_duplicate_ids_and_unverified_ready_deployment() -> None:
    duplicate = _ledger_payload()
    duplicate["attempts"][1]["attempt_id"] = "attempt-a"
    with pytest.raises(ValidationError, match="duplicate attempt_id"):
        AttemptLedger.model_validate(duplicate)

    unverified = _ledger_payload()
    unverified["deployment"]["configuration_verification"]["service_tier_verified"] = False
    with pytest.raises(ValidationError, match="exact deployment verification"):
        AttemptLedger.model_validate(unverified)

    snapshot = _ledger_payload()
    snapshot["deployment"]["configuration_verification"]["provider_snapshot_verified"] = False
    with pytest.raises(ValidationError, match="snapshot is not verified"):
        AttemptLedger.model_validate(snapshot)

    wrong_provider = _ledger_payload()
    wrong_provider["attempts"][0]["serving_provider"] = "fallback-provider"
    with pytest.raises(ValidationError, match="provider does not match"):
        AttemptLedger.model_validate(wrong_provider)

    wrong_tier = _ledger_payload()
    wrong_tier["attempts"][0]["service_tier"] = "priority"
    with pytest.raises(ValidationError, match="service tier does not match"):
        AttemptLedger.model_validate(wrong_tier)

    wrong_model = _ledger_payload()
    wrong_model["attempts"][0]["resolved_model_id"] = "provider/fallback-model"
    with pytest.raises(ValidationError, match="identity does not match"):
        AttemptLedger.model_validate(wrong_model)

    wrong_region = _ledger_payload()
    wrong_region["attempts"][0]["data_region"] = "eu"
    with pytest.raises(ValidationError, match="region does not match"):
        AttemptLedger.model_validate(wrong_region)


def test_attempt_cost_requires_evidence_and_preserves_partial_cost_count() -> None:
    invalid = _ledger_payload()
    invalid["attempts"][0]["cost_evidence_id"] = None
    with pytest.raises(ValidationError, match="requires billing evidence"):
        AttemptLedger.model_validate(invalid)

    partial = _ledger_payload()
    partial["attempts"][1]["observed_cost_usd"] = None
    partial["attempts"][1]["billing_evidence"] = "none"
    partial["attempts"][1]["cost_evidence_id"] = None
    result = aggregate_attempt_ledger(AttemptLedger.model_validate(partial))
    cost = next(item for item in result.metric_summaries if item.metric == "observed_cost_usd")
    assert cost.observation_count == 2
    assert result.economics_records == ()
    assert "cost observed on 2 of 3 attempts" in result.diagnostics


def test_attempt_ledger_rejects_observation_free_or_reviewed_fact_ready_input() -> None:
    empty = _ledger_payload()
    for attempt in empty["attempts"]:
        for field in (
            "input_tokens",
            "output_tokens",
            "reasoning_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "turns",
            "agent_steps",
            "wall_seconds",
            "tool_calls",
            "retry_count",
            "observed_cost_usd",
        ):
            attempt[field] = None
        attempt["billing_evidence"] = "none"
        attempt["cost_evidence_id"] = None
    with pytest.raises(ValidationError, match="no operational observations"):
        AttemptLedger.model_validate(empty)

    reviewed = _ledger_payload()
    reviewed["capture_type"] = "reviewed_fact_extract"
    with pytest.raises(ValidationError, match="raw or archived source artifact"):
        AttemptLedger.model_validate(reviewed)


def test_attempt_aggregate_cli_consumes_frozen_yaml_offline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger_path = tmp_path / "ledger.yaml"
    ledger_path.write_text(yaml.safe_dump(_ledger_payload(), sort_keys=True), encoding="utf-8")
    args = build_parser().parse_args(
        ["attempts", "aggregate", "--ledger", str(ledger_path)]
    )
    assert run(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["attempt_count"] == 3
    assert payload["successful_attempts"] == 2
    assert payload["economics_records"][0]["mean_cost_usd"] == 3
