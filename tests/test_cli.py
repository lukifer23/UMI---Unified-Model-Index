import csv
import json
from pathlib import Path

import pytest

from umi.cli import build_parser, run

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    "command",
    ["validate", "rank", "estimates", "uncertainty", "sensitivity", "correlations", "pareto"],
)
def test_every_cli_command_emits_json(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        [
            command,
            "--data-dir",
            str(ROOT / "tests" / "fixtures"),
            "--config-dir",
            str(ROOT / "tests" / "fixtures" / "config"),
        ]
    )
    assert run(args) == 0
    assert json.loads(capsys.readouterr().out) is not None


def test_rank_csv_is_flat_and_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    rendered = []
    for _ in range(2):
        args = build_parser().parse_args(
            [
                "rank",
                "--data-dir",
                str(ROOT / "tests" / "fixtures"),
                "--config-dir",
                str(ROOT / "tests" / "fixtures" / "config"),
                "--format",
                "csv",
            ]
        )
        assert run(args) == 0
        rendered.append(capsys.readouterr().out)
    assert rendered[0] == rendered[1]
    rows = list(csv.DictReader(rendered[0].splitlines()))
    assert len(rows) == 5
    assert "capability.score" in rows[0]
    assert "source_record_ids" in rows[0]


def test_estimates_are_not_serialized_as_a_ranking(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        [
            "estimates",
            "--data-dir",
            str(ROOT / "data" / "pilots" / "v0.3" / "raw"),
            "--config-dir",
            str(ROOT / "config"),
        ]
    )
    assert run(args) == 0
    estimates = json.loads(capsys.readouterr().out)
    assert len(estimates) == 5
    assert all("rank" not in item for item in estimates)
    assert {item["publication_label"] for item in estimates} == {
        "real evidence — model-specific partial estimate"
    }


def test_fixture_config_is_auto_discovered(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        ["validate", "--data-dir", str(ROOT / "tests" / "fixtures")]
    )
    assert run(args) == 0
    assert json.loads(capsys.readouterr().out)["scoring_ready"] is True


@pytest.mark.parametrize(
    "source", ["aa", "epoch", "epoch-benchmarks", "arena-agent", "arena-text", "deepswe"]
)
def test_v03_ingest_commands_are_offline_and_deterministic(
    source: str, capsys: pytest.CaptureFixture[str]
) -> None:
    arguments = [
        "ingest",
        "--source",
        source,
        "--crosswalk",
        str(ROOT / "data" / "sources" / "v0.3" / "crosswalk.yaml"),
    ]
    rendered = []
    for _ in range(2):
        assert run(build_parser().parse_args(arguments)) == 0
        rendered.append(capsys.readouterr().out)
    assert rendered[0] == rendered[1]


def test_v03_policy_and_publication_commands(capsys: pytest.CaptureFixture[str]) -> None:
    pilot = str(ROOT / "data" / "pilots" / "v0.3" / "raw")
    config = str(ROOT / "config")
    registry = str(ROOT / "data" / "sources" / "registry.yaml")
    crosswalk = str(ROOT / "data" / "sources" / "v0.3" / "crosswalk.yaml")
    sources_args = build_parser().parse_args(
        [
            "sources",
            "validate",
            "--data-dir",
            pilot,
            "--config-dir",
            config,
            "--source-registry",
            registry,
            "--crosswalk",
            crosswalk,
        ]
    )
    assert run(sources_args) == 0
    source_report = json.loads(capsys.readouterr().out)
    assert source_report["schema_valid"] is True
    assert source_report["crosswalk_valid"] is True

    for command in ("crosswalk", "overlap"):
        arguments = [command]
        if command == "crosswalk":
            arguments += [
                "--data-dir",
                pilot,
                "--source-registry",
                registry,
                "--crosswalk",
                crosswalk,
            ]
        else:
            arguments += ["--config-dir", config]
        assert run(build_parser().parse_args(arguments)) == 0
        assert json.loads(capsys.readouterr().out)["valid"] is True

    rank_args = build_parser().parse_args(
        [
            "rank",
            "--data-dir",
            pilot,
            "--config-dir",
            config,
            "--include-provisional",
        ]
    )
    assert run(rank_args) == 0
    ranked = json.loads(capsys.readouterr().out)
    assert len(ranked) == 5
    assert all(item["rank"] is None and item["headline_overall"] is None for item in ranked)
    assert {item["publication_label"] for item in ranked} == {
        "real evidence — model-specific partial estimate"
    }
