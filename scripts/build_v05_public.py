"""Offline builder and check for UMI Public v0.5 artifacts."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from umi.edition import load_public_edition_config
from umi.public import score_public_edition, write_public_artifacts
from umi.public_candidates import audit_named_candidates
from umi.public_eligibility import decide_public_eligibility

V04_SCORES = {
    "gpt-5.6-sol-max": 66.26583886547628,
    "kimi-k3-max": 59.69066272741414,
    "claude-opus-5-max": 55.510021169743936,
    "claude-fable-5-max": 54.429636426057556,
    "glm-5.2-max": 54.202702676964044,
}


def check() -> None:
    edition = load_public_edition_config(edition="v0.5")
    decision = decide_public_eligibility(edition)
    if decision.certified:
        raise SystemExit("v0.5 unexpectedly claims certified_public_score")
    payload = score_public_edition(edition_name="v0.5")
    if payload["certified"]:
        raise SystemExit("v0.5 live payload is certified")
    by_id = {item["entity_id"]: item["umi_public"] for item in payload["models"]}
    for entity_id, expected in V04_SCORES.items():
        if not math.isclose(by_id[entity_id], expected, abs_tol=1e-12):
            raise SystemExit(f"v0.5 drifted from frozen v0.4: {entity_id}")
    audits = audit_named_candidates()
    if audits["headline_additions"]:
        raise SystemExit("named candidates entered the headline")
    print(
        f"v0.5 check passed state={payload['publication_state']} "
        f"reasons={decision.reason_codes}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    if args.check:
        check()
        return
    destination = Path(args.output_dir) if args.output_dir else None
    payload = write_public_artifacts(destination, edition_name="v0.5")
    print(f"edition={payload['edition_id']} state={payload['publication_state']}")


if __name__ == "__main__":
    main()