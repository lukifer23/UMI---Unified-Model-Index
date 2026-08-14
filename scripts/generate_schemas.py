from __future__ import annotations

from pathlib import Path

from umi.schema_export import generate_schemas

if __name__ == "__main__":
    generate_schemas(Path(__file__).parents[1] / "schemas")
