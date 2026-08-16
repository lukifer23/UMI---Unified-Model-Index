from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).parents[1]
DEFAULT_FACTS = ROOT / "data" / "sources" / "v0.3" / "deepswe-reviewed-facts-2026-08-13.yaml"


def _read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "UMI-acquisition/0.3.13"})
    with urllib.request.urlopen(  # noqa: S310 - explicit acquisition verifier
        request, timeout=120
    ) as response:
        return cast(bytes, response.read())


def _mean(rows: list[dict[str, Any]], field: str) -> tuple[float, int]:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    if not values:
        raise ValueError(f"DeepSWE ledger has no observations for {field}")
    return math.fsum(values) / len(values), len(values)


def verify_trial_ledger(payload: bytes, facts: dict[str, Any]) -> dict[str, object]:
    ledger_contract = cast(dict[str, Any], facts["upstream_trial_ledger"])
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != ledger_contract["sha256"]:
        raise ValueError(
            "DeepSWE trial-ledger checksum changed: "
            f"expected {ledger_contract['sha256']}, got {actual_sha256}"
        )
    ledger = cast(dict[str, Any], json.loads(payload))
    all_rows = cast(list[dict[str, Any]], ledger["rows"])
    if int(ledger["n_trials"]) != int(ledger_contract["declared_trial_count"]):
        raise ValueError("DeepSWE declared trial count changed")

    selected_configs = {str(row["source_config_id"]) for row in facts["rows"]}
    selected_rows = [row for row in all_rows if row.get("config") in selected_configs]
    scored_rows = [row for row in selected_rows if row.get("included_in_score") is True]
    if len(selected_rows) != int(ledger_contract["selected_configuration_rows"]):
        raise ValueError("DeepSWE selected configuration count changed")
    if len(scored_rows) != int(ledger_contract["included_scored_rows"]):
        raise ValueError("DeepSWE scored-row count changed")

    metric_fields = {
        "mean_cost_usd": "cost_usd",
        "mean_input_tokens": "n_input_tokens",
        "mean_output_tokens": "n_output_tokens",
        "mean_cached_tokens": "n_cache_tokens",
        "mean_duration_seconds": "agent_duration_seconds",
        "mean_agent_steps": "n_agent_steps",
    }
    reconciled_rows: list[dict[str, object]] = []
    for fact_row in cast(list[dict[str, Any]], facts["rows"]):
        config_id = str(fact_row["source_config_id"])
        rows = [row for row in scored_rows if row["config"] == config_id]
        attempts = len(rows)
        successes = sum(bool(row["passed"]) for row in rows)
        if attempts != int(fact_row["attempted_tasks"]):
            raise ValueError(f"DeepSWE attempt count changed for {config_id}")
        if successes != int(fact_row["passed_attempts"]):
            raise ValueError(f"DeepSWE success count changed for {config_id}")
        if {str(row["provider"]) for row in rows} != {str(fact_row["serving_provider"])}:
            raise ValueError(f"DeepSWE serving provider changed for {config_id}")
        source_rate = float(fact_row["pass_rate"])
        if not math.isclose(source_rate, successes / attempts, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"DeepSWE pass rate changed for {config_id}")

        observation_counts: dict[str, int] = {}
        for fact_field, ledger_field in metric_fields.items():
            value, count = _mean(rows, ledger_field)
            if not math.isclose(
                value,
                float(fact_row[fact_field]),
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError(f"DeepSWE {fact_field} changed for {config_id}")
            observation_counts[fact_field] = count
        resource_observation_count = int(fact_row["resource_observation_count"])
        resource_fields = tuple(field for field in metric_fields if field != "mean_cost_usd")
        if any(
            observation_counts[field] != resource_observation_count for field in resource_fields
        ):
            raise ValueError(f"DeepSWE resource denominator changed for {config_id}")
        if observation_counts["mean_cost_usd"] != int(fact_row["cost_observation_count"]):
            raise ValueError(f"DeepSWE cost denominator changed for {config_id}")
        reconciled_rows.append(
            {
                "source_config_id": config_id,
                "attempts": attempts,
                "successful_attempts": successes,
                "serving_provider": fact_row["serving_provider"],
                "observation_counts": observation_counts,
            }
        )

    return {
        "status": "verified",
        "source_url": ledger_contract["url"],
        "sha256": actual_sha256,
        "declared_trial_count": ledger["n_trials"],
        "selected_configuration_rows": len(selected_rows),
        "included_scored_rows": len(scored_rows),
        "excluded_error_rows": len(selected_rows) - len(scored_rows),
        "rows": reconciled_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the facts-only DeepSWE extract against its official trial ledger"
    )
    parser.add_argument(
        "--accept-network",
        action="store_true",
        help="Required acknowledgement that this verifier performs one HTTP request",
    )
    parser.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    args = parser.parse_args()
    if not args.accept_network:
        parser.error("--accept-network is required")
    facts = cast(dict[str, Any], yaml.safe_load(args.facts.read_text(encoding="utf-8")))
    ledger_contract = cast(dict[str, Any], facts["upstream_trial_ledger"])
    report = verify_trial_ledger(_read_url(str(ledger_contract["url"])), facts)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
