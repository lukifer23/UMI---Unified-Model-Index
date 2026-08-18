"""Offline builder and freeze check for UMI Public v0.4 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from umi.public import score_public_edition, write_public_artifacts

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = {
    "data/editions/v0.4/processed/model-scores.json": (
        "0c4256c585966e63d9b67b2d5e64f23e62c17718bf1a7030d01f1e6a3786006c"
    ),
    "data/editions/v0.4/processed/common-core.json": (
        "83c7819c5792798ce67b062ce70d6ab592d47d2733c0f4425e64ecdb9e0152dd"
    ),
    "data/editions/v0.4/processed/rejected-evidence.json": (
        "aa04375010e6cd01c2c417f09374030b3a83e452b612762d2f033dcc75eb8d44"
    ),
}
V04_SCORES = {
    "gpt-5.6-sol-max": 66.26583886547628,
    "kimi-k3-max": 59.69066272741414,
    "claude-opus-5-max": 55.510021169743936,
    "claude-fable-5-max": 54.429636426057556,
    "glm-5.2-max": 54.202702676964044,
}


def check() -> None:
    for relative, digest_expected in GOLDEN.items():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if digest != digest_expected:
            raise SystemExit(f"v0.4 freeze drift: {relative}")
    stored = json.loads(
        (ROOT / "data/editions/v0.4/processed/model-scores.json").read_text(encoding="utf-8")
    )
    live = score_public_edition(edition_name="v0.4")
    by_id = {item["entity_id"]: item["umi_public"] for item in stored["models"]}
    live_by_id = {item["entity_id"]: item["umi_public"] for item in live["models"]}
    for entity_id, score_expected in V04_SCORES.items():
        if not math.isclose(by_id[entity_id], score_expected, abs_tol=1e-12):
            raise SystemExit(f"v0.4 stored score drift: {entity_id}")
        if not math.isclose(live_by_id[entity_id], score_expected, abs_tol=1e-12):
            raise SystemExit(f"v0.4 live score drift: {entity_id}")
    print("v0.4 freeze check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
        return
    payload = write_public_artifacts(edition_name="v0.4")
    print(f"edition={payload['edition_id']} state={payload['publication_state']}")


if __name__ == "__main__":
    main()
