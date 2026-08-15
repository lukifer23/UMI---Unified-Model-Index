from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).parents[1]
ARENA_REVISION = "08dd89df7a8aa9df2ead3799f6422af4ad2e97a7"


def _read_url(url: str, *, attempts: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "UMI-acquisition/0.3.5"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(  # noqa: S310 - explicit acquisition script
                request, timeout=30
            ) as response:
                return cast(bytes, response.read())
        except (HTTPError, URLError):
            if attempt + 1 == attempts:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable acquisition retry state")


def _download(url: str, destination: Path) -> None:
    destination.write_bytes(_read_url(url))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _zip_content_sha256(path: Path) -> str:
    """Hash member names and bytes while ignoring mutable ZIP container metadata."""
    with zipfile.ZipFile(path) as archive:
        members = [
            {"path": name, "sha256": hashlib.sha256(archive.read(name)).hexdigest()}
            for name in sorted(archive.namelist())
            if not name.endswith("/")
        ]
    payload = json.dumps(members, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire openly redistributable v0.3 artifacts")
    parser.add_argument(
        "--accept-network",
        action="store_true",
        help="Required acknowledgement that this acquisition script performs HTTP requests",
    )
    parser.add_argument(
        "--snapshot-id",
        required=True,
        help="Stable caller-supplied snapshot ID; timestamps are never generated implicitly",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        help="Fresh output directory; defaults to data/sources/acquisitions/SNAPSHOT_ID",
    )
    args = parser.parse_args()
    if not args.accept_network:
        parser.error("--accept-network is required")
    destination = args.destination or ROOT / "data" / "sources" / "acquisitions" / args.snapshot_id
    destination.mkdir(parents=True, exist_ok=False)
    epoch_url = "https://epoch.ai/data/eci_benchmarks.csv"
    epoch_path = destination / "epoch-eci-benchmarks.csv"
    _download(epoch_url, epoch_path)
    artifacts: list[dict[str, object]] = [
        {"path": epoch_path.name, "url": epoch_url, "sha256": _sha256(epoch_path)}
    ]
    benchmark_data_url = "https://epoch.ai/data/benchmark_data.zip"
    benchmark_data_path = destination / "epoch-benchmark-data.zip"
    _download(benchmark_data_url, benchmark_data_path)
    artifacts.append(
        {
            "path": benchmark_data_path.name,
            "url": benchmark_data_url,
            "sha256": _sha256(benchmark_data_path),
            "content_sha256": _zip_content_sha256(benchmark_data_path),
        }
    )
    arena_base = (
        "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/resolve/"
        f"{ARENA_REVISION}"
    )
    for source_path, output in (
        ("agent/latest-00000-of-00001.parquet", "arena-agent-latest.parquet"),
        (
            "text_style_control/latest-00000-of-00001.parquet",
            "arena-text-style-control-latest.parquet",
        ),
    ):
        url = f"{arena_base}/{source_path}?download=true"
        output_path = destination / output
        _download(url, output_path)
        artifacts.append(
            {
                "path": output_path.name,
                "url": url,
                "upstream_revision": ARENA_REVISION,
                "sha256": _sha256(output_path),
            }
        )
    (destination / "manifest.json").write_text(
        json.dumps(
            {"snapshot_id": args.snapshot_id, "artifacts": artifacts},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
