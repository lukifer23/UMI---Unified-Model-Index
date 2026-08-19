"""Build the deterministic UMI Public v0.6 source-audit artifacts offline."""

from __future__ import annotations

from analysis.v06_source_audit_dashboard import write_v06_source_audit_dashboard
from umi.v06_source_audit import write_v06_source_audit


def main() -> None:
    report = write_v06_source_audit()
    dashboard = write_v06_source_audit_dashboard(report=report)
    print(f"edition={report['edition_id']} state={report['publication_state']}")
    print(f"headline_eligible={report['headline_eligible']}")
    print(f"unresolved={','.join(report['unresolved_requirement_ids'])}")
    print(f"charts={','.join(item['id'] for item in dashboard['charts'])}")


if __name__ == "__main__":
    main()
