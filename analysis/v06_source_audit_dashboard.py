"""Portable visual report for the v0.6 strict public-source audit."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from umi.v06_source_audit import ROOT, build_v06_source_audit


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _gate_chart(gates: dict[str, Any]) -> str:
    width, left, row_height, top = 760, 185, 42, 40
    usable = width - left - 90
    height = top + len(gates) * row_height + 18
    pieces = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Headline gate progress">',
        '<text x="12" y="20" font-size="14" font-weight="600" '
        'fill="#111827">Headline gate progress</text>',
    ]
    for index, (name, gate) in enumerate(gates.items()):
        y = top + index * row_height
        observed, required = float(gate["observed"]), float(gate["required"])
        scale = max(required, 1.0)
        observed_width = usable * min(observed / scale, 1.0)
        required_x = left + usable * min(required / scale, 1.0)
        color = "#15803d" if gate["passes"] else "#b45309"
        pieces.extend(
            [
                f'<text x="8" y="{y + 18}" font-size="11" fill="#374151">{_escape(name)}</text>',
                f'<rect x="{left}" y="{y + 4}" width="{usable}" height="20" '
                'rx="4" fill="#e5e7eb"></rect>',
                f'<rect x="{left}" y="{y + 4}" width="{observed_width:.2f}" '
                f'height="20" rx="4" fill="{color}"></rect>',
                f'<line x1="{required_x:.2f}" y1="{y + 1}" '
                f'x2="{required_x:.2f}" y2="{y + 27}" stroke="#111827" '
                'stroke-width="2"></line>',
                f'<text x="{left + usable + 8}" y="{y + 18}" font-size="11" '
                f'fill="#111827">{observed:.1%} / {required:.1%}</text>',
            ]
        )
    pieces.append("</svg>")
    return "".join(pieces)


def _requirement_chart(requirements: list[dict[str, Any]]) -> str:
    width, left, row_height, top = 760, 300, 34, 40
    height = top + len(requirements) * row_height + 18
    pieces = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Public source requirement status">',
        '<text x="12" y="20" font-size="14" font-weight="600" '
        'fill="#111827">Public source requirement status</text>',
    ]
    for index, requirement in enumerate(requirements):
        y = top + index * row_height
        color = "#15803d" if requirement["passes"] else "#b45309"
        label = "admitted" if requirement["passes"] else "blocked"
        pieces.extend(
            [
                f'<text x="8" y="{y + 17}" font-size="11" fill="#374151">'
                f'{_escape(requirement["requirement_id"])}</text>',
                f'<rect x="{left}" y="{y + 2}" width="210" height="22" '
                f'rx="4" fill="{color}"></rect>',
                f'<text x="{left + 105}" y="{y + 17}" font-size="11" '
                f'text-anchor="middle" fill="white">{label}</text>',
            ]
        )
    pieces.append("</svg>")
    return "".join(pieces)


def _partial_score_cell(model: dict[str, Any]) -> str:
    value = model["v05_governed_partial_score"]
    return "not scored" if value is None else f"{float(value):.2f}"


def build_v06_source_audit_dashboard(report: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = report or build_v06_source_audit()
    return {
        "surface": "v0.6-public-source-audit-dashboard",
        "edition_id": audit["edition_id"],
        "publication_scope": audit["publication_scope"],
        "publication_state": audit["publication_state"],
        "headline_eligible": False,
        "headline_overall": None,
        "evidence_snapshot_cutoff": audit["evidence_snapshot_cutoff"],
        "source_audit_fingerprint": audit["source_audit_fingerprint"],
        "gates": audit["gates"],
        "requirements": audit["requirements"],
        "source_artifacts": audit["source_artifacts"],
        "models": audit["models"],
        "unresolved_requirement_ids": audit["unresolved_requirement_ids"],
        "charts": [
            {"id": "gate_progress", "title": "Headline gate progress"},
            {"id": "source_requirements", "title": "Public source requirement status"},
        ],
    }


def render_v06_source_audit_dashboard_html(dashboard: dict[str, Any]) -> str:
    gate_rows = "".join(
        "<tr>"
        f"<td>{_escape(name)}</td><td>{gate['observed']:.1%}</td>"
        f"<td>{gate['required']:.1%}</td><td>{'pass' if gate['passes'] else 'blocked'}</td>"
        "</tr>"
        for name, gate in dashboard["gates"].items()
    )
    requirement_rows = "".join(
        "<tr>"
        f"<td><code>{_escape(item['requirement_id'])}</code></td>"
        f"<td>{_escape(', '.join(item['source_artifact_ids']) or 'none')}</td>"
        f"<td>{'admitted' if item['passes'] else 'blocked'}</td>"
        f"<td>{_escape('; '.join(item['failures']) or 'all constraints satisfied')}</td>"
        "</tr>"
        for item in dashboard["requirements"]
    )
    source_rows = "".join(
        "<tr>"
        f"<td><code>{_escape(item['artifact_id'])}</code></td>"
        f"<td>{_escape(item['redistribution_scope'])}</td>"
        f"<td>{'verified' if item['checksum_valid'] else 'mismatch'}</td>"
        f"<td>{_escape(item['source_organization'])}</td>"
        "</tr>"
        for item in dashboard["source_artifacts"]
    )
    model_rows = "".join(
        "<tr>"
        f"<td><code>{_escape(item['entity_id'])}</code></td>"
        f"<td>{_partial_score_cell(item)}</td>"
        f"<td>{item['gates']['capability']['observed']:.1%}</td>"
        f"<td>{item['gates']['efficiency']['observed']:.1%}</td>"
        f"<td>{item['gates']['economics']['observed']:.1%}</td>"
        "<td>withheld</td></tr>"
        for item in dashboard["models"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UMI Public v0.6 verified source audit</title>
<style>
body{{font:15px/1.5 system-ui,sans-serif;margin:24px auto;max-width:980px;color:#111827}}
h1,h2{{line-height:1.2}}
.meta,.note{{color:#4b5563}}
.callout{{background:#fff7ed;border-left:4px solid #b45309;padding:12px 16px;margin:16px 0 24px}}
table{{border-collapse:collapse;width:100%;margin:16px 0 28px}}
th,td{{border-bottom:1px solid #e5e7eb;padding:8px 6px;text-align:left;vertical-align:top}}
th{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#6b7280}}
svg{{width:100%;height:auto;margin:8px 0 24px}}
code{{font-size:13px}}
</style>
</head>
<body>
<h1>UMI Public v0.6 verified source audit</h1>
<p class="meta">Evidence cutoff <code>{_escape(dashboard['evidence_snapshot_cutoff'])}</code>
/ fingerprint <code>{_escape(dashboard['source_audit_fingerprint'])}</code></p>
<div class="callout"><strong>Headline Overall is withheld.</strong>
This report verifies frozen public evidence and its gaps. It does not turn v0.5 governed partials,
calculated costs, or reviewed facts into a v0.6 Overall score.</div>
{_gate_chart(dashboard['gates'])}
<table><thead><tr><th>Gate</th><th>Observed</th><th>Required</th><th>Status</th></tr></thead>
<tbody>{gate_rows}</tbody></table>
{_requirement_chart(dashboard['requirements'])}
<h2>Why source requirements remain blocked</h2>
<table><thead><tr><th>Requirement</th><th>Frozen sources</th><th>Status</th>
<th>Failure</th></tr></thead>
<tbody>{requirement_rows}</tbody></table>
<h2>Artifact integrity and rights</h2>
<table><thead><tr><th>Artifact</th><th>Redistribution</th><th>Checksum</th><th>Organization</th></tr></thead>
<tbody>{source_rows}</tbody></table>
<h2>Exact pilot coverage</h2>
<p class="note">The governed partial column is v0.5 context only, not a v0.6 score or rank.</p>
<table><thead><tr><th>Configuration</th><th>v0.5 partial</th><th>Capability</th>
<th>Efficiency</th><th>Economics</th><th>v0.6 Overall</th></tr></thead>
<tbody>{model_rows}</tbody></table>
</body>
</html>"""


def write_v06_source_audit_dashboard(
    output_dir: Path | None = None,
    *,
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    audit = report or build_v06_source_audit()
    dashboard = build_v06_source_audit_dashboard(audit)
    destination = output_dir or ROOT / "data" / "editions" / "v0.6" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "public-source-audit-dashboard.json").write_text(
        json.dumps(dashboard, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "public-source-audit-dashboard.html").write_text(
        render_v06_source_audit_dashboard_html(dashboard), encoding="utf-8"
    )
    return dashboard
