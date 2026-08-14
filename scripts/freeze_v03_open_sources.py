from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parents[1]
DESTINATION = ROOT / "data" / "sources" / "v0.3"
ARENA_REVISION = "08dd89df7a8aa9df2ead3799f6422af4ad2e97a7"


def _download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response:  # noqa: S310 - explicit acquisition script
        destination.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire openly redistributable v0.3 artifacts")
    parser.add_argument(
        "--accept-network",
        action="store_true",
        help="Required acknowledgement that this acquisition script performs HTTP requests",
    )
    args = parser.parse_args()
    if not args.accept_network:
        parser.error("--accept-network is required")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    _download(
        "https://epoch.ai/data/eci_benchmarks.csv",
        DESTINATION / "epoch-eci-benchmarks-2026-08-14.csv",
    )
    endpoint = "https://datasets-server.huggingface.co/rows"
    for subset, output in (
        ("agent", "arena-agent-2026-08-14.json"),
        ("text_style_control", "arena-text-style-control-2026-08-14.json"),
    ):
        query = urllib.parse.urlencode(
            {
                "dataset": "lmarena-ai/leaderboard-dataset",
                "config": subset,
                "split": "train",
                "offset": 0,
                "length": 100,
                "revision": ARENA_REVISION,
            }
        )
        with urllib.request.urlopen(f"{endpoint}?{query}") as response:  # noqa: S310
            payload = json.loads(response.read())
        (DESTINATION / output).write_text(
            json.dumps(payload, separators=(",", ":")), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
