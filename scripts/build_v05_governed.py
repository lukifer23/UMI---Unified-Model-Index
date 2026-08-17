"""Offline builder for UMI Public v0.5 Governed artifacts."""

from __future__ import annotations

from umi.public import write_public_artifacts


def main() -> None:
    payload = write_public_artifacts(edition_name="v0.5")
    print(f"edition={payload['edition_id']} state={payload['publication_state']}")
    print(f"valid={payload['validation']['valid']}")
    for item in sorted(payload["models"], key=lambda row: row["rank"]):
        print(
            f"{item['rank']} {item['entity_id']}: public={item['umi_public']:.6f} "
            f"cap={item['capability']:.6f}"
        )


if __name__ == "__main__":
    main()
