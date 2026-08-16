from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from analysis.claims import calibrate_release_claims
from analysis.compare import common_capability_comparison
from analysis.correlations import benchmark_correlations
from analysis.gaps import pilot_gap_report
from analysis.pareto_metrics import pareto_dimensions
from analysis.pilot_sensitivity import analyze_pilot_sensitivity
from analysis.rankings import rank_results
from analysis.references import reference_observations
from analysis.sensitivity import analyze_sensitivity
from analysis.uncertainty import source_bound_capability_sensitivity
from analysis.value_sensitivity import analyze_value_sensitivity
from umi.adapters import (
    adapt_aa_facts,
    adapt_aa_gdpval_facts,
    adapt_aa_lcr_facts,
    adapt_aa_omniscience_facts,
    adapt_aa_tau3_facts,
    adapt_aa_terminalbench_facts,
    adapt_arena_json,
    adapt_cursorbench_facts,
    adapt_deepswe_facts,
    adapt_epoch_benchmarks_zip,
    adapt_epoch_csv,
    adapt_lab_release_facts,
)
from umi.attempt_ledger import aggregate_attempt_ledger, load_attempt_ledger
from umi.bundle import (
    build_acceptance_manifest,
    load_scoring_bundle,
    validate_scoring_bundle,
)
from umi.certificate import build_comparison_certificate
from umi.config import load_project_config
from umi.controlled_eval import load_run_manifest, load_task_pack, operational_preflight
from umi.loading import load_dataset, load_model_crosswalk, load_source_registry
from umi.scoring import score_bundle, score_dataset
from umi.source_policy import (
    overlap_report,
    source_readiness_matrix,
    validate_crosswalk,
    validate_overlap,
)
from umi.validation import DataValidationError, validate_dataset, validate_source_registry


def _primitive(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _primitive(value.model_dump(mode="json"))
    if is_dataclass(value) and not isinstance(value, type):
        return _primitive(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitive(item) for item in value]
    return value


def _flatten(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in value.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            output.update(_flatten(item, full_key))
        elif isinstance(item, list):
            output[full_key] = "|".join(str(part) for part in item)
        else:
            output[full_key] = item
    return output


def _emit(payload: Any, output_format: str, output: str | None) -> None:
    primitive = _primitive(payload)
    destination = Path(output) if output else None
    if output_format == "json":
        rendered = json.dumps(primitive, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if destination:
            destination.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return
    rows = primitive if isinstance(primitive, list) else [primitive]
    flattened = [_flatten(row) for row in rows]
    fieldnames = sorted({key for row in flattened for key in row})
    handle = destination.open("w", newline="", encoding="utf-8") if destination else sys.stdout
    try:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened)
    finally:
        if destination:
            handle.close()


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument(
        "--config-dir",
        help="Configuration directory; defaults to DATA_DIR/config when present, otherwise config",
    )
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output")
    parser.add_argument("--source-registry", default="data/sources/registry.yaml")
    parser.add_argument("--crosswalk", default="data/sources/v0.3/crosswalk.yaml")
    parser.add_argument(
        "--allow-unready",
        action="store_true",
        help="Development-only: score unready records provisionally; headlines remain suppressed",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="umi", description="Unified Model Index CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "validate",
        "rank",
        "estimates",
        "sensitivity",
        "value-sensitivity",
        "references",
        "correlations",
        "pareto",
        "pilot-sensitivity",
        "compare",
        "certificate",
        "uncertainty",
        "claims",
        "gaps",
    ):
        child = subparsers.add_parser(command)
        _add_common(child)
    subparsers.choices["validate"].set_defaults(source_registry=None, crosswalk=None)
    subparsers.choices["compare"].add_argument("--models", nargs="+", required=True)
    subparsers.choices["certificate"].add_argument("--models", nargs="+", required=True)
    sources = subparsers.add_parser("sources")
    source_commands = sources.add_subparsers(dest="sources_command", required=True)
    source_validate = source_commands.add_parser("validate")
    _add_common(source_validate)
    source_validate.add_argument(
        "--strict",
        action="store_true",
        help="Validate the complete audit package, including diagnostic evidence",
    )

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument(
        "--source",
        required=True,
        choices=(
            "aa",
            "aa-hle",
            "aa-gdpval",
            "aa-lcr",
            "aa-omniscience",
            "aa-terminalbench",
            "aa-tau3",
            "cursorbench",
            "epoch",
            "epoch-benchmarks",
            "arena-agent",
            "arena-text",
            "deepswe",
            "lab-anthropic",
            "lab-openai",
            "lab-kimi",
            "lab-zai",
        ),
    )
    ingest.add_argument("--artifact")
    ingest.add_argument("--crosswalk", default="data/sources/v0.3/crosswalk.yaml")
    ingest.add_argument("--format", choices=("json", "csv"), default="json")
    ingest.add_argument("--output")

    crosswalk = subparsers.add_parser("crosswalk")
    crosswalk.add_argument("--data-dir", default="data/pilots/v0.3/raw")
    crosswalk.add_argument("--crosswalk", default="data/sources/v0.3/crosswalk.yaml")
    crosswalk.add_argument("--source-registry", default="data/sources/registry.yaml")
    crosswalk.add_argument("--format", choices=("json", "csv"), default="json")
    crosswalk.add_argument("--output")

    overlap = subparsers.add_parser("overlap")
    overlap.add_argument("--config-dir", default="config")
    overlap.add_argument("--format", choices=("json", "csv"), default="json")
    overlap.add_argument("--output")
    bundle = subparsers.add_parser("bundle")
    bundle_commands = bundle.add_subparsers(dest="bundle_command", required=True)
    bundle_validate = bundle_commands.add_parser("validate")
    _add_common(bundle_validate)
    attempts = subparsers.add_parser("attempts")
    attempt_commands = attempts.add_subparsers(dest="attempts_command", required=True)
    attempt_aggregate = attempt_commands.add_parser("aggregate")
    attempt_aggregate.add_argument("--ledger", required=True)
    attempt_aggregate.add_argument("--format", choices=("json", "csv"), default="json")
    attempt_aggregate.add_argument("--output")
    operational = subparsers.add_parser("operational")
    operational_commands = operational.add_subparsers(
        dest="operational_command", required=True
    )
    operational_preflight_parser = operational_commands.add_parser("preflight")
    operational_preflight_parser.add_argument("--task-pack", required=True)
    operational_preflight_parser.add_argument("--run-manifest", required=True)
    operational_preflight_parser.add_argument(
        "--format", choices=("json", "csv"), default="json"
    )
    operational_preflight_parser.add_argument("--output")
    return parser


def _adapt_source(args: argparse.Namespace) -> Any:
    root = Path("data/sources/v0.3")
    crosswalk = load_model_crosswalk(args.crosswalk)
    defaults = {
        "aa": root / "aa-reviewed-facts-2026-08-14.yaml",
        "aa-hle": root / "aa-hle-reviewed-facts-2026-08-14.yaml",
        "aa-gdpval": root / "aa-gdpval-reviewed-facts-2026-08-15.yaml",
        "aa-lcr": root / "aa-lcr-reviewed-facts-2026-08-15.yaml",
        "aa-omniscience": root / "aa-omniscience-reviewed-facts-2026-08-15.yaml",
        "aa-terminalbench": root / "aa-terminalbench-reviewed-facts-2026-08-15.yaml",
        "aa-tau3": root / "aa-tau3-reviewed-facts-2026-08-15.yaml",
        "cursorbench": root / "cursorbench-reviewed-facts-2026-08-14.yaml",
        "epoch": root / "epoch-eci-benchmarks-2026-08-14.csv",
        "epoch-benchmarks": root / "epoch-benchmark-data-2026-08-14.zip",
        "arena-agent": root / "arena-agent-2026-08-14.json",
        "arena-text": root / "arena-text-style-control-2026-08-14.json",
        "deepswe": root / "deepswe-reviewed-facts-2026-08-13.yaml",
        "lab-anthropic": root / "anthropic-release-facts-2026-08-14.yaml",
        "lab-openai": root / "openai-release-facts-2026-08-14.yaml",
        "lab-kimi": root / "kimi-release-facts-2026-08-14.yaml",
        "lab-zai": root / "zai-release-facts-2026-08-14.yaml",
    }
    artifact = Path(args.artifact) if args.artifact else defaults[args.source]
    if args.source in {"aa", "aa-hle"}:
        return adapt_aa_facts(artifact, crosswalk)
    if args.source == "aa-gdpval":
        return adapt_aa_gdpval_facts(artifact, crosswalk)
    if args.source == "aa-lcr":
        return adapt_aa_lcr_facts(artifact, crosswalk)
    if args.source == "aa-omniscience":
        return adapt_aa_omniscience_facts(artifact, crosswalk)
    if args.source == "aa-terminalbench":
        return adapt_aa_terminalbench_facts(artifact, crosswalk)
    if args.source == "aa-tau3":
        return adapt_aa_tau3_facts(artifact, crosswalk)
    if args.source == "cursorbench":
        return adapt_cursorbench_facts(artifact, crosswalk)
    if args.source == "epoch":
        return adapt_epoch_csv(
            artifact,
            crosswalk,
            source_id="epoch-eci",
            artifact_id="epoch-eci-matrix-2026-08-14",
        )
    if args.source == "epoch-benchmarks":
        return adapt_epoch_benchmarks_zip(
            artifact,
            crosswalk,
            source_id="epoch-benchmarks",
            artifact_id="epoch-benchmark-data-2026-08-14",
        )
    if args.source in {"arena-agent", "arena-text"}:
        return adapt_arena_json(
            artifact,
            crosswalk,
            source_id=args.source,
            artifact_id=f"{args.source}-2026-08-14",
            upstream_revision="08dd89df7a8aa9df2ead3799f6422af4ad2e97a7",
            subset="agent" if args.source == "arena-agent" else "text_style_control",
        )
    if args.source.startswith("lab-"):
        return adapt_lab_release_facts(artifact, crosswalk)
    return adapt_deepswe_facts(artifact, crosswalk)


def run(args: argparse.Namespace) -> int:
    if args.command == "operational":
        operational_report = operational_preflight(
            load_task_pack(args.task_pack), load_run_manifest(args.run_manifest)
        )
        _emit(operational_report, args.format, args.output)
        return 0 if operational_report["valid"] else 1
    if args.command == "attempts":
        _emit(
            aggregate_attempt_ledger(load_attempt_ledger(args.ledger)),
            args.format,
            args.output,
        )
        return 0
    if args.command == "ingest":
        _emit(_adapt_source(args), args.format, args.output)
        return 0
    if args.command == "crosswalk":
        crosswalk_policy_report = validate_crosswalk(
            load_model_crosswalk(args.crosswalk),
            load_dataset(args.data_dir),
            load_source_registry(args.source_registry),
        )
        _emit(crosswalk_policy_report, args.format, args.output)
        return 0 if crosswalk_policy_report.valid else 1
    if args.command == "overlap":
        config = load_project_config(args.config_dir)
        overlap_policy_report = validate_overlap(config.overlap)
        _emit(
            {
                "valid": overlap_policy_report.valid,
                "errors": overlap_policy_report.errors,
                **overlap_report(config),
            },
            args.format,
            args.output,
        )
        return 0 if overlap_policy_report.valid else 1

    colocated_config = Path(args.data_dir) / "config"
    config_dir = args.config_dir or (colocated_config if colocated_config.is_dir() else "config")
    config = load_project_config(config_dir)
    dataset = load_dataset(args.data_dir)
    if args.command == "bundle":
        bundle = load_scoring_bundle(
            args.data_dir,
            config_dir,
            args.source_registry,
            args.crosswalk,
        )
        _emit(
            {
                "schema_valid": True,
                "scored_inputs_ready": True,
                "strict_audit_valid": None,
                "headline_eligible": None,
                "model_count": len(bundle.dataset.models),
                "scored_audit_fingerprint": bundle.dataset.scored_audit_fingerprint,
                "acceptance_manifest": bundle.acceptance_manifest,
                "warnings": bundle.warnings,
            },
            args.format,
            args.output,
        )
        return 0
    if args.command == "sources":
        registry = load_source_registry(args.source_registry)
        data_report = validate_dataset(dataset, config)
        crosswalk = load_model_crosswalk(args.crosswalk)
        if args.strict:
            registry_report = validate_source_registry(
                registry, args.source_registry, dataset
            )
            crosswalk_report = validate_crosswalk(crosswalk, dataset, registry)
            audit_errors = (
                *data_report.errors,
                *registry_report.errors,
                *crosswalk_report.errors,
            )
        else:
            manifest = build_acceptance_manifest(dataset, registry)
            accepted_artifact_ids = set(manifest.accepted_artifact_ids)
            accepted_crosswalk_ids = set(manifest.accepted_crosswalk_entry_ids)
            audit_errors = validate_scoring_bundle(
                dataset, config, registry, args.source_registry, crosswalk
            )
            registry_report = validate_source_registry(
                registry,
                args.source_registry,
                snapshot_ids=accepted_artifact_ids,
            )
            crosswalk_report = validate_crosswalk(
                crosswalk.model_copy(
                    update={
                        "entries": tuple(
                            item
                            for item in crosswalk.entries
                            if item.id in accepted_crosswalk_ids
                        )
                    }
                )
            )
        source_payload = {
            "schema_valid": data_report.schema_valid,
            "scored_inputs_ready": data_report.scored_inputs_ready,
            "strict_audit_valid": not audit_errors if args.strict else None,
            "headline_eligible": None,
            "bundle_valid": not audit_errors,
            "crosswalk_valid": crosswalk_report.valid,
            "source_errors": registry_report.errors,
            "crosswalk_errors": crosswalk_report.errors,
            "audit_errors": tuple(sorted(set(audit_errors))),
            "readiness": source_readiness_matrix(dataset),
        }
        _emit(source_payload, args.format, args.output)
        return 0 if data_report.schema_valid and not audit_errors else 1
    if args.command == "validate":
        report = validate_dataset(dataset, config)
        source_report = None
        if args.source_registry:
            source_report = validate_source_registry(
                load_source_registry(args.source_registry), args.source_registry, dataset
            )
        _emit(
            {
                "schema_valid": report.schema_valid,
                "scored_inputs_ready": report.scored_inputs_ready,
                "strict_audit_valid": None,
                "headline_eligible": None,
                "errors": report.errors,
                "readiness_failures": report.readiness_failures,
                "warnings": report.warnings,
                "source_errors": source_report.errors if source_report is not None else (),
                "source_warnings": source_report.warnings if source_report is not None else (),
            },
            args.format,
            args.output,
        )
        return 0 if report.schema_valid else 1
    real_dataset = any(not model.synthetic for model in dataset.models)
    if real_dataset:
        bundle = load_scoring_bundle(
            args.data_dir,
            config_dir,
            args.source_registry,
            args.crosswalk,
        )
        dataset = bundle.dataset
        config = bundle.config
        results = score_bundle(bundle, allow_unready=args.allow_unready)
    else:
        results = score_dataset(dataset, config, allow_unready=args.allow_unready)
    payload: Any
    if args.command == "references":
        payload = reference_observations(dataset)
    elif args.command == "certificate":
        if not real_dataset:
            raise ValueError("comparison certificates require a governed real-data bundle")
        payload = build_comparison_certificate(bundle, tuple(args.models))
    elif args.command == "compare":
        payload = common_capability_comparison(dataset, config, tuple(args.models))
    elif args.command == "uncertainty":
        payload = source_bound_capability_sensitivity(dataset, config)
    elif args.command == "claims":
        payload = calibrate_release_claims(dataset)
    elif args.command == "gaps":
        payload = pilot_gap_report(dataset, config)
    elif args.command == "rank":
        ranked = rank_results(results)
        payload = [{"rank": item.rank, **item.result.model_dump(mode="json")} for item in ranked]
    elif args.command == "estimates":
        payload = [item.model_dump(mode="json") for item in results]
    elif args.command == "sensitivity":
        payload = analyze_sensitivity(results, config)
    elif args.command == "value-sensitivity":
        payload = analyze_value_sensitivity(results, config)
    elif args.command == "correlations":
        payload = benchmark_correlations(
            dataset, config.normalization.correlation_min_overlap, config
        )
    elif args.command == "pareto":
        payload = pareto_dimensions(dataset, results)
    else:
        payload = analyze_pilot_sensitivity(dataset, config)
    _emit(payload, args.format, args.output)
    return 0


def main() -> int:
    try:
        return run(build_parser().parse_args())
    except (FileNotFoundError, ValueError, ValidationError, DataValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
