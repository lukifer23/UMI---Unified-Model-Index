from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from analysis.references import reference_observations
from umi.cli import build_parser, run
from umi.config import load_project_config
from umi.economics import score_economics
from umi.loading import load_dataset, load_source_registry
from umi.schemas import CostBasis
from umi.scoring import score_dataset
from umi.validation import validate_dataset, validate_source_registry

ROOT = Path(__file__).parents[1]


def test_real_pilot_is_traceable_but_not_headline_eligible() -> None:
    dataset = load_dataset(ROOT / "data" / "raw")
    config = load_project_config(ROOT / "config")
    registry_path = ROOT / "data" / "sources" / "registry.yaml"
    registry = load_source_registry(registry_path)

    report = validate_dataset(dataset, config)
    source_report = validate_source_registry(registry, registry_path, dataset)
    assert not report.errors
    assert not source_report.errors
    assert len(dataset.models) == 6
    assert len(dataset.benchmarks) == 10
    assert len(dataset.external_indexes) == 6
    assert len(dataset.task_economics) == 6
    observations = reference_observations(dataset)
    assert len(observations) == 12
    assert all(item.scoring_role == "reference_only" for item in observations)

    results = score_dataset(dataset, config)
    assert all(not item.eligible for item in results)
    assert all(item.headline_overall is None for item in results)
    assert all(item.value is None for item in results)
    assert all(item.evaluation_date.isoformat() == "2026-07-17" for item in results)
    assert all(
        any("attempted-task cost excluded" in message for message in item.diagnostics)
        for item in results
    )
    # The complete external index is retained but never smuggled into Capability.
    glm = next(item for item in results if item.model_id == "glm-5.2-max")
    assert glm.capability.score is None
    assert glm.partial_overall_estimate is None


def test_source_registry_detects_capture_tampering() -> None:
    path = ROOT / "data" / "sources" / "registry.yaml"
    registry = load_source_registry(path)
    bad_snapshot = registry.snapshots[0].model_copy(update={"artifact_sha256": "0" * 64})
    report = validate_source_registry(
        registry.model_copy(update={"snapshots": (bad_snapshot,)}), path
    )
    assert any("checksum mismatch" in error for error in report.errors)


def test_successful_task_cost_can_score_but_attempted_cost_cannot() -> None:
    dataset = load_dataset(ROOT / "data" / "raw")
    config = load_project_config(ROOT / "config")
    attempted = score_economics(dataset, config).components
    assert all(item.score is None for item in attempted.values())

    successful = dataset.model_copy(
        update={
            "task_economics": tuple(
                item.model_copy(update={"cost_basis": CostBasis.SUCCESSFUL_TASK})
                for item in dataset.task_economics
            )
        }
    )
    scored = score_economics(successful, config).components
    assert all(item.score is not None for item in scored.values())
    assert scored["muse-spark-1.1-xhigh"].score > scored["claude-fable-5-max-fallback"].score


def test_real_pilot_cli_validates_registry_and_exports_stable_csv(
    capsys: pytest.CaptureFixture[str],
) -> None:
    validate_args = build_parser().parse_args(
        [
            "validate",
            "--data-dir",
            str(ROOT / "data" / "raw"),
            "--config-dir",
            str(ROOT / "config"),
            "--source-registry",
            str(ROOT / "data" / "sources" / "registry.yaml"),
        ]
    )
    assert run(validate_args) == 0
    assert '"valid": true' in capsys.readouterr().out

    reference_args = build_parser().parse_args(
        [
            "references",
            "--data-dir",
            str(ROOT / "data" / "raw"),
            "--config-dir",
            str(ROOT / "config"),
            "--format",
            "csv",
        ]
    )
    assert run(reference_args) == 0
    rows = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert len(rows) == 12
    assert set(rows[0]) == {
        "cohort_key",
        "measurement_type",
        "metric_id",
        "model_id",
        "record_id",
        "scoring_role",
        "unit_or_basis",
        "value",
    }
