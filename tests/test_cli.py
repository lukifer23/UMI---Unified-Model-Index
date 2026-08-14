import csv
import json
from pathlib import Path

import pytest

from umi.cli import build_parser, run

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("command", ["validate", "rank", "sensitivity", "correlations", "pareto"])
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


def test_fixture_config_is_auto_discovered(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        ["validate", "--data-dir", str(ROOT / "tests" / "fixtures")]
    )
    assert run(args) == 0
    assert json.loads(capsys.readouterr().out)["scoring_ready"] is True
