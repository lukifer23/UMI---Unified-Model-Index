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
    args = build_parser().parse_args(["validate", "--data-dir", str(ROOT / "tests" / "fixtures")])
    assert run(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["schema_valid"] is True
    assert report["scored_inputs_ready"] is True
    assert report["strict_audit_valid"] is None
    assert args.source_registry is None


@pytest.mark.parametrize(
    "source",
    [
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
    ],
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
            "--strict",
        ]
    )
    assert run(sources_args) == 0
    source_report = json.loads(capsys.readouterr().out)
    assert source_report["schema_valid"] is True
    assert source_report["strict_audit_valid"] is True
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

    rank_args = build_parser().parse_args(["rank", "--data-dir", pilot, "--config-dir", config])
    assert run(rank_args) == 0
    ranked = json.loads(capsys.readouterr().out)
    assert ranked == []


def test_model_specific_rank_flag_is_removed() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["rank", "--include-provisional"])


def test_certificate_cli_emits_the_governed_certificate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = build_parser().parse_args(
        [
            "certificate",
            "--data-dir",
            str(ROOT / "data" / "pilots" / "v0.3" / "raw"),
            "--config-dir",
            str(ROOT / "config"),
            "--models",
            "claude-opus-5-max",
            "kimi-k3-max",
            "glm-5.2-max",
        ]
    )
    assert run(args) == 0
    certificate = json.loads(capsys.readouterr().out)
    assert certificate["status"] == "provisional_comparison"
    assert certificate["certificate_version"] == "umi-certificate-v0.1"
    assert certificate["source_artifact_checksums"]
    assert certificate["result_fingerprint"]


def test_edition_validate_and_score_v04(capsys: pytest.CaptureFixture[str]) -> None:
    validate_args = build_parser().parse_args(["edition", "--edition", "v0.4", "validate"])
    assert run(validate_args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["valid"] is True
    assert report["edition"] == "umi-public-v0.4"

    score_args = build_parser().parse_args(["edition", "--edition", "v0.4", "score"])
    assert run(score_args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["publication_state"] == "published"
    assert len(payload["models"]) == 5
    assert all(item["umi_public"] is not None for item in payload["models"])


def test_legacy_edition_validate_reports_infeasible(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = build_parser().parse_args(["edition", "--edition", "v0.3", "validate"])
    assert run(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["valid"] is False
    assert report["legacy_policy_mode"] is True
