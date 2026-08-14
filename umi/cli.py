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

from analysis.correlations import benchmark_correlations
from analysis.pareto_metrics import pareto_dimensions
from analysis.rankings import rank_results
from analysis.references import reference_observations
from analysis.sensitivity import analyze_sensitivity
from analysis.value_sensitivity import analyze_value_sensitivity
from umi.config import load_project_config
from umi.loading import load_dataset, load_source_registry
from umi.scoring import score_dataset
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
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output")
    parser.add_argument("--source-registry")
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
        "sensitivity",
        "value-sensitivity",
        "references",
        "correlations",
        "pareto",
    ):
        child = subparsers.add_parser(command)
        _add_common(child)
    subparsers.choices["rank"].add_argument(
        "--include-provisional",
        action="store_true",
        help="Include models not eligible for headlines",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    config = load_project_config(args.config_dir)
    dataset = load_dataset(args.data_dir)
    if args.command == "validate":
        report = validate_dataset(dataset, config)
        if args.source_registry:
            source_report = validate_source_registry(
                load_source_registry(args.source_registry), args.source_registry, dataset
            )
            report = type(report)(
                errors=tuple(sorted({*report.errors, *source_report.errors})),
                warnings=tuple(sorted({*report.warnings, *source_report.warnings})),
                readiness_failures=report.readiness_failures,
            )
        _emit(
            {
                "schema_valid": report.schema_valid,
                "scoring_ready": report.scoring_ready,
                "errors": report.errors,
                "readiness_failures": report.readiness_failures,
                "warnings": report.warnings,
            },
            args.format,
            args.output,
        )
        return 0 if report.scoring_ready else 1
    results = score_dataset(dataset, config, allow_unready=args.allow_unready)
    payload: Any
    if args.command == "references":
        payload = reference_observations(dataset)
    elif args.command == "rank":
        ranked = rank_results(results, eligible_only=not args.include_provisional)
        payload = [{"rank": item.rank, **item.result.model_dump(mode="json")} for item in ranked]
    elif args.command == "sensitivity":
        payload = analyze_sensitivity(results, config)
    elif args.command == "value-sensitivity":
        payload = analyze_value_sensitivity(results, config)
    elif args.command == "correlations":
        payload = benchmark_correlations(
            dataset, config.normalization.correlation_min_overlap, config
        )
    else:
        payload = pareto_dimensions(dataset, results)
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
