from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, datetime
from pathlib import Path

from umi.adapters.common import exact_entry, identifier
from umi.adapters.models import AdaptationResult, AdapterRejection
from umi.schemas import (
    ArtifactCaptureType,
    BenchmarkMeasurement,
    ConfigurationVerification,
    MeasurementUncertainty,
    ModelCrosswalk,
    ResultType,
    ScoringDisposition,
    SignalRole,
    Source,
    UncertaintyKind,
)

PILOT_SOURCE_MODELS = {
    "claude-opus-5_max",
    "claude-fable-5_max",
    "gpt-5.6-sol_max",
    "kimi-k3_max",
    "glm-5.2_max",
}

EXTERNAL_BENCHMARKS = (
    {
        "member": "scicode_external.csv",
        "benchmark_id": "scicode",
        "value_field": "Score",
        "benchmark_version": "scicode-test-288",
        "harness_version": "aa-intelligence-v4.1.1-public-methodology",
        "cohort_key": "aa-v4.1.1-scicode-test-288-background-pass1",
        "number_of_tasks": 288,
        "repeats": 3,
        "metric_definition": (
            "SciCode test-subproblem pass@1 score in percent with scientist background prompting"
        ),
        "methodology_url": "https://artificialanalysis.ai/methodology/intelligence-benchmarking",
    },
    {
        "member": "critpt_external.csv",
        "benchmark_id": "critpt",
        "value_field": "Accuracy",
        "benchmark_version": "critpt-public-leaderboard-2026-08-14",
        "harness_version": "aa-intelligence-v4.1.1-public-methodology",
        "cohort_key": "aa-v4.1.1-critpt-70-test-challenges-pass1",
        "number_of_tasks": 70,
        "repeats": 5,
        "metric_definition": "CritPt official-grader pass@1 accuracy in percent",
        "methodology_url": "https://artificialanalysis.ai/methodology/intelligence-benchmarking",
    },
)

ARC_AGI_2_DISPLAY_NAMES = {
    "claude-opus-5_max": "Claude Opus 5 (Max)",
    "gpt-5.6-sol_max": "GPT-5.6 Sol (Max)",
    "kimi-k3_max": "Kimi K3 (Max)",
}


def adapt_epoch_benchmarks_zip(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
) -> AdaptationResult:
    """Adapt all promoted pilot benchmarks from one frozen Epoch archive."""
    gpqa = adapt_epoch_gpqa_zip(
        path, crosswalk, source_id=source_id, artifact_id=artifact_id
    )
    external = adapt_epoch_external_benchmarks_zip(
        path, crosswalk, source_id=source_id, artifact_id=artifact_id
    )
    arc_agi_2 = adapt_epoch_arc_agi_2_zip(
        path, crosswalk, source_id=source_id, artifact_id=artifact_id
    )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="epoch-benchmark-zip-v2",
        benchmarks=(*gpqa.benchmarks, *external.benchmarks, *arc_agi_2.benchmarks),
        rejections=(*gpqa.rejections, *external.rejections, *arc_agi_2.rejections),
    )


def adapt_epoch_arc_agi_2_zip(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
) -> AdaptationResult:
    """Adapt exact verified ARC-AGI-2 Max rows and reject label/effort conflicts."""
    source = Source.model_validate(
        {
            "organization": "Epoch AI",
            "url": "https://epoch.ai/data/benchmark_data.zip",
            "accessed": date(2026, 8, 14),
        }
    )
    with zipfile.ZipFile(path) as archive:
        payload = archive.read("arc_agi_2_external.csv").decode("utf-8")

    records: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []
    relevant_source_ids = {*ARC_AGI_2_DISPLAY_NAMES, "glm-5.2_unknown"}
    for row in csv.DictReader(io.StringIO(payload)):
        source_model_id = row["Model version"]
        if source_model_id not in relevant_source_ids:
            continue
        expected_display_name = ARC_AGI_2_DISPLAY_NAMES.get(source_model_id)
        if expected_display_name is not None and row["Name"] != expected_display_name:
            rejected.append(
                AdapterRejection(
                    source_row_id=f"arc_agi_2_external.csv:{row['id']}",
                    reason=(
                        f"source/display effort conflict: {source_model_id} is Max but "
                        f"display label is {row['Name']!r}"
                    ),
                )
            )
            continue
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(
                    source_row_id=f"arc_agi_2_external.csv:{row['id']}",
                    reason="no exact Max-effort crosswalk",
                )
            )
            continue
        cost_per_task = float(row["Cost per task"]) if row["Cost per task"] else None
        records.append(
            BenchmarkMeasurement(
                record_id=identifier(
                    f"epoch-arc-agi-2-{match.canonical_model_id}-{row['id']}"
                ),
                benchmark_id="arc-agi-2",
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=float(row["Score"]) * 100.0,
                cohort_key="arc-prize-verified-arc-agi-2-semi-private-pass2",
                evaluation_date=None,
                model_release_date=date.fromisoformat(row["Release date"]),
                measurement_as_of_date=date(2026, 8, 14),
                evaluation_settings={
                    "source_archive_member": "arc_agi_2_external.csv",
                    "source_row_key": row["id"],
                    "source_display_name": row["Name"],
                    "source_cost_per_task_usd": cost_per_task,
                    "evaluation_set": "semi-private",
                    "attempts_per_test_output": 2,
                    "methodology_url": "https://arcprize.org/policy",
                },
                number_of_tasks=120,
                pass_at_k=2,
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version="arc-agi-2-semi-private-120",
                harness_version="arc-prize-verified-policy-2026-08-14",
                metric_definition=(
                    "Percent of semi-private ARC-AGI-2 tasks solved with up to two exact-grid "
                    "predictions per test output"
                ),
                evaluator="ARC Prize Foundation",
                harness_owner="ARC Prize Foundation",
                run_executor="ARC Prize Foundation",
                tools_enabled=False,
                raw_artifact_available=True,
                capture_type=ArtifactCaptureType.RAW_UPSTREAM_PAYLOAD,
                reproducible=False,
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="arc-agi-2",
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                notes=(
                    "ARC Prize verified-leaderboard result redistributed by Epoch. Cost per task "
                    "is preserved as source metadata but does not enter Economics without exact "
                    "deployment and billing provenance. Evaluation date is not exposed."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="epoch-arc-agi-2-zip-v1",
        benchmarks=tuple(records),
        rejections=tuple(rejected),
    )


def adapt_epoch_gpqa_zip(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
) -> AdaptationResult:
    """Adapt the exact pilot rows from Epoch's frozen GPQA Diamond export."""
    source = Source.model_validate(
        {
            "organization": "Epoch AI",
            "url": "https://epoch.ai/data/benchmark_data.zip",
            "accessed": date(2026, 8, 14),
        }
    )
    with zipfile.ZipFile(path) as archive:
        payload = archive.read("gpqa_diamond.csv").decode("utf-8")

    records: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []
    for row in csv.DictReader(io.StringIO(payload)):
        source_model_id = row["Model version"]
        if source_model_id not in PILOT_SOURCE_MODELS:
            continue
        match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
        if match is None or match.canonical_model_id is None:
            rejected.append(
                AdapterRejection(source_row_id=source_model_id, reason="no exact crosswalk")
            )
            continue
        evaluated = datetime.fromisoformat(row["Started at"].replace("Z", "+00:00")).date()
        records.append(
            BenchmarkMeasurement(
                record_id=identifier(f"epoch-gpqa-{match.canonical_model_id}-{row['id']}"),
                benchmark_id="gpqa-diamond",
                model_id=match.canonical_model_id,
                source_model_id=source_model_id,
                value=float(row["mean_score"]) * 100.0,
                cohort_key="epoch-gpqa-diamond-1.0.6-simple-evals",
                evaluation_date=evaluated,
                model_release_date=date.fromisoformat(row["Release date"]),
                measurement_as_of_date=date(2026, 8, 14),
                evaluation_settings={
                    "prompt_family": "simple-evals-zero-shot-chain-of-thought",
                    "answer_format": "ANSWER: LETTER",
                    "temperature": "provider_api_default",
                    "question_count": 198,
                    "source_run_id": row["id"],
                    "logs_url": row["Logs"] or None,
                },
                number_of_tasks=198,
                uncertainty=MeasurementUncertainty(
                    kind=UncertaintyKind.STANDARD_ERROR,
                    standard_error=float(row["stderr"]) * 100.0,
                    source_fields=("stderr",),
                    notes="Standard error published by Epoch; trial count is not inferred.",
                ),
                source=source,
                result_type=ResultType.INDEPENDENT,
                benchmark_version="gpqa-diamond-1.0.6",
                harness_version="epoch-inspect-simple-evals-gpqa-1.0.6",
                metric_definition="Mean GPQA Diamond accuracy in percent across the published run",
                evaluator="Epoch AI",
                harness_owner="Epoch AI",
                run_executor="Epoch AI",
                raw_artifact_available=True,
                capture_type=ArtifactCaptureType.RAW_UPSTREAM_PAYLOAD,
                reproducible=False,
                configuration_verification=ConfigurationVerification(
                    model_label_exact=True,
                    release_label_exact=True,
                    effort_label_exact=True,
                    fallback_absent=True,
                ),
                source_artifact_id=artifact_id,
                source_registry_snapshot_id=artifact_id,
                crosswalk_entry_id=match.id,
                signal_id="gpqa-diamond",
                signal_role=SignalRole.TASK,
                scoring_disposition=ScoringDisposition.SCORED,
                notes=(
                    "Raw Epoch export retained. Exact provider endpoint and trial count are not "
                    "claimed; those omissions do not block provisional Capability use."
                ),
            )
        )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="epoch-gpqa-zip-v1",
        benchmarks=tuple(records),
        rejections=tuple(rejected),
    )


def adapt_epoch_external_benchmarks_zip(
    path: str | Path,
    crosswalk: ModelCrosswalk,
    *,
    source_id: str,
    artifact_id: str,
) -> AdaptationResult:
    """Adapt configured creator-run benchmark rows from Epoch's frozen raw export."""
    source = Source.model_validate(
        {
            "organization": "Epoch AI",
            "url": "https://epoch.ai/data/benchmark_data.zip",
            "accessed": date(2026, 8, 14),
        }
    )
    records: list[BenchmarkMeasurement] = []
    rejected: list[AdapterRejection] = []
    with zipfile.ZipFile(path) as archive:
        for spec in EXTERNAL_BENCHMARKS:
            member = str(spec["member"])
            number_of_tasks = spec["number_of_tasks"]
            repeats = spec["repeats"]
            if not isinstance(number_of_tasks, int) or not isinstance(repeats, int):
                raise TypeError(f"invalid task/repeat profile for {member}")
            payload = archive.read(member).decode("utf-8")
            for row in csv.DictReader(io.StringIO(payload)):
                source_model_id = row["Model version"]
                if source_model_id not in PILOT_SOURCE_MODELS:
                    continue
                match = exact_entry(crosswalk, source_id, artifact_id, source_model_id)
                if match is None or match.canonical_model_id is None:
                    rejected.append(
                        AdapterRejection(
                            source_row_id=f"{member}:{source_model_id}",
                            reason="no exact crosswalk",
                        )
                    )
                    continue
                benchmark_id = str(spec["benchmark_id"])
                source_row_key = row.get("id") or source_model_id
                records.append(
                    BenchmarkMeasurement(
                        record_id=identifier(
                            f"epoch-{benchmark_id}-{match.canonical_model_id}-{source_row_key}"
                        ),
                        benchmark_id=identifier(benchmark_id),
                        model_id=match.canonical_model_id,
                        source_model_id=source_model_id,
                        value=float(row[str(spec["value_field"])]) * 100.0,
                        cohort_key=identifier(str(spec["cohort_key"])),
                        evaluation_date=None,
                        model_release_date=date.fromisoformat(row["Release date"]),
                        measurement_as_of_date=date(2026, 8, 14),
                        evaluation_settings={
                            "source_archive_member": member,
                            "source_row_key": source_row_key,
                            "source_display_name": row.get("Name") or None,
                            "methodology_url": spec["methodology_url"],
                            "methodology_profile": "Artificial Analysis Intelligence Index v4.1.1",
                            "repeats": repeats,
                        },
                        number_of_tasks=number_of_tasks,
                        number_of_trials=number_of_tasks * repeats,
                        pass_at_k=1,
                        source=source,
                        result_type=ResultType.INDEPENDENT,
                        benchmark_version=str(spec["benchmark_version"]),
                        harness_version=str(spec["harness_version"]),
                        metric_definition=str(spec["metric_definition"]),
                        evaluator="Artificial Analysis",
                        harness_owner=(
                            "SciCode benchmark authors"
                            if benchmark_id == "scicode"
                            else "CritPt benchmark authors"
                        ),
                        run_executor="Artificial Analysis",
                        raw_artifact_available=True,
                        capture_type=ArtifactCaptureType.RAW_UPSTREAM_PAYLOAD,
                        reproducible=False,
                        configuration_verification=ConfigurationVerification(
                            model_label_exact=True,
                            release_label_exact=True,
                            effort_label_exact=True,
                            fallback_absent=True,
                        ),
                        source_artifact_id=artifact_id,
                        source_registry_snapshot_id=artifact_id,
                        crosswalk_entry_id=match.id,
                        signal_id=identifier(benchmark_id),
                        signal_role=SignalRole.TASK,
                        scoring_disposition=ScoringDisposition.SCORED,
                        notes=(
                            "Creator-run result redistributed by Epoch under CC BY 4.0. The export "
                            "does not establish an evaluation date; measurement_as_of_date is kept "
                            "separate. Protocol facts follow the cited official AA v4.1.1 "
                            "methodology."
                        ),
                    )
                )
    return AdaptationResult(
        source_id=source_id,
        adapter_id="epoch-external-benchmarks-zip-v1",
        benchmarks=tuple(records),
        rejections=tuple(rejected),
    )
