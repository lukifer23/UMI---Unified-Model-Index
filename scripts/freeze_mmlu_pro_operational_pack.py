from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as parquet

from umi.controlled_eval import canonical_fingerprint
from umi.schemas import ControlledTaskPack

ROOT = Path(__file__).parents[1]
REVISION = "b189ec765aa7ed75c8acfea42df31fdae71f97be"
SOURCE_SHA256 = "0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8"
SOURCE_FILE = "data/test-00000-of-00001.parquet"
SOURCE_URL = (
    "https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/"
    f"{REVISION}/{SOURCE_FILE}?download=true"
)
SEED = "umi-mmlu-pro-operational-pilot-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download(destination: Path) -> None:
    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": "UMI-acquisition/0.3.14"}
    )
    with urllib.request.urlopen(  # noqa: S310 - explicit, revision-pinned acquisition
        request, timeout=60
    ) as response:
        destination.write_bytes(cast(bytes, response.read()))


def _selection_key(row: dict[str, Any]) -> str:
    identity = f"{SEED}|{row['category']}|{row['question_id']}|{row['_row_index']}"
    return hashlib.sha256(identity.encode()).hexdigest()


def _slug(value: str) -> str:
    return "-".join(value.lower().split())


def _build_pack(source: Path, tasks_per_category: int) -> dict[str, Any]:
    table = parquet.read_table(source)
    rows = table.to_pylist()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row_index, raw in enumerate(rows):
        row = cast(dict[str, Any], raw)
        row["_row_index"] = row_index
        grouped[str(row["category"])].append(row)
    selected = [
        row
        for category in sorted(grouped)
        for row in sorted(grouped[category], key=_selection_key)[:tasks_per_category]
    ]
    tasks = []
    for row in selected:
        row_index = int(row["_row_index"])
        question_id = int(row["question_id"])
        category = str(row["category"])
        tasks.append(
            {
                "task_id": f"mmlu-pro-{_slug(category)}-{question_id}-{row_index}",
                "source_row_index": row_index,
                "source_question_id": question_id,
                "category": category,
                "source_subset": str(row["src"]),
                "question": str(row["question"]),
                "options": [str(option) for option in row["options"]],
                "correct_answer": str(row["answer"]),
                "correct_answer_index": int(row["answer_index"]),
            }
        )
    source_counts = {key: len(value) for key, value in sorted(grouped.items())}
    selected_counts = dict(sorted(Counter(str(row["category"]) for row in selected).items()))
    payload: dict[str, Any] = {
        "pack_version": "umi-controlled-task-pack-v0.1",
        "pack_id": "mmlu-pro-test-balanced-70-v1",
        "source_dataset": "TIGER-Lab/MMLU-Pro",
        "source_revision": REVISION,
        "source_file": SOURCE_FILE,
        "source_file_sha256": SOURCE_SHA256,
        "license_id": "mit",
        "config": "default",
        "split": "test",
        "selection_algorithm": (
            "For each category, ascending SHA256 of "
            "SEED|category|question_id|zero_based_source_row_index; take first N"
        ),
        "selection_seed": SEED,
        "tasks_per_category": tasks_per_category,
        "category_source_counts": source_counts,
        "category_selected_counts": selected_counts,
        "tasks": tasks,
    }
    payload["fingerprint"] = canonical_fingerprint(payload)
    ControlledTaskPack.model_validate(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Freeze the revision-pinned MMLU-Pro operational pilot cohort"
    )
    parser.add_argument("--accept-network", action="store_true")
    parser.add_argument(
        "--use-existing-source",
        action="store_true",
        help="Verify and reuse source-output without performing a network request",
    )
    parser.add_argument("--source-output", type=Path, required=True)
    parser.add_argument("--pack-output", type=Path, required=True)
    parser.add_argument("--tasks-per-category", type=int, default=5)
    args = parser.parse_args()
    if not args.accept_network and not args.use_existing_source:
        parser.error("--accept-network or --use-existing-source is required")
    if args.accept_network and args.use_existing_source:
        parser.error("choose exactly one of --accept-network or --use-existing-source")
    if args.tasks_per_category <= 0:
        parser.error("--tasks-per-category must be positive")
    if args.pack_output.exists():
        parser.error(f"refusing to overwrite existing path: {args.pack_output}")
    args.pack_output.parent.mkdir(parents=True, exist_ok=True)
    if args.use_existing_source:
        if not args.source_output.is_file():
            parser.error(f"existing source not found: {args.source_output}")
    else:
        if args.source_output.exists():
            parser.error(f"refusing to overwrite existing path: {args.source_output}")
        args.source_output.parent.mkdir(parents=True, exist_ok=True)
        _download(args.source_output)
    if _sha256(args.source_output) != SOURCE_SHA256:
        args.source_output.unlink()
        raise ValueError("downloaded MMLU-Pro parquet checksum mismatch")
    payload = _build_pack(args.source_output, args.tasks_per_category)
    args.pack_output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
