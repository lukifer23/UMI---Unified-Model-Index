"""Offline builder for UMI Public v0.4 artifacts."""

from __future__ import annotations

from umi.public import write_public_artifacts


def main() -> None:
    payload = write_public_artifacts()
    models = payload["models"]
    print(f"edition={payload['edition_id']} state={payload['publication_state']}")
    for item in models:
        print(
            f"{item['entity_id']}: capability={item['capability']} "
            f"opeff={item['operational_efficiency']} public={item['umi_public']}"
        )


if __name__ == "__main__":
    main()
