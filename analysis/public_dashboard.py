"""Presentation-only UMI Public charts. Does not rescore."""

from __future__ import annotations

import csv
import html
import io
import json
from pathlib import Path
from typing import Any

from umi.edition import load_public_edition_config

SHORT_NAMES = {
    "claude-opus-5-max": "Opus 5",
    "claude-fable-5-max": "Fable 5",
    "gpt-5.6-sol-max": "Sol",
    "kimi-k3-max": "Kimi K3",
    "glm-5.2-max": "GLM-5.2",
}
SERIES_LABELS = {
    "epoch-chess-puzzles": "Chess puzzles",
    "deepswe-v1.1-pass1": "DeepSWE Pass@1",
    "epoch-scicode": "SciCode",
    "epoch-weirdml": "WeirdML",
    "epoch-gpqa": "GPQA Diamond",
    "epoch-otis-aime": "OTIS Mock AIME",
    "epoch-critpt": "CritPt",
    "deepswe-output-tokens": "DeepSWE tokens",
    "deepswe-agent-steps": "DeepSWE steps",
    "weirdml-cost-per-run": "WeirdML cost/run",
}
COMPONENT_COLORS = {
    "capability": "#1d4ed8",
    "operational_efficiency": "#c2410c",
    "access_economics": "#047857",
    "umi_public": "#111827",
}


def _round(value: float) -> float:
    return round(float(value), 6)


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def chart_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    weights = load_public_edition_config().weights.overall
    rows: list[dict[str, Any]] = []
    for item in sorted(payload["models"], key=lambda row: row["rank"]):
        capability = float(item["capability"])
        opeff = float(item["operational_efficiency"])
        access = float(item["access_economics"])
        public = float(item["umi_public"])
        rows.append(
            {
                "rank": item["rank"],
                "entity_id": item["entity_id"],
                "named_release": item["named_release"],
                "entity_kind": item["entity_kind"],
                "short_name": SHORT_NAMES[item["entity_id"]],
                "capability": _round(capability),
                "operational_efficiency": _round(opeff),
                "access_economics": _round(access),
                "umi_public": _round(public),
                "capability_weighted": _round(weights.capability * capability),
                "operational_efficiency_weighted": _round(
                    weights.operational_efficiency * opeff
                ),
                "access_economics_weighted": _round(weights.access_economics * access),
                "interval": None,
                "interval_status": "unpublished_point_extracts",
            }
        )
    return rows


def series_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = (
        ("capability", "capability_series"),
        ("operational_efficiency", "operational_series"),
        ("access_economics", "access_series"),
    )
    for item in sorted(payload["models"], key=lambda row: row["rank"]):
        for component, field in groups:
            for series_id, detail in sorted(item[field].items()):
                rows.append(
                    {
                        "entity_id": item["entity_id"],
                        "short_name": SHORT_NAMES[item["entity_id"]],
                        "component": component,
                        "series_id": series_id,
                        "series_label": SERIES_LABELS.get(series_id, series_id),
                        "raw": _round(detail["raw"]),
                        "score": _round(detail["score"]),
                    }
                )
    return rows


def build_public_dashboard(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("publication_state") != "published":
        raise ValueError("public dashboard requires published umi_public scores")
    models = payload["models"]
    if any(item.get("umi_public") is None for item in models):
        raise ValueError("public dashboard refuses to plot a null umi_public as zero")
    edition = load_public_edition_config()
    ranking = chart_rows(payload)
    return {
        "surface": "public-dashboard",
        "edition_id": payload["edition_id"],
        "formula_version": payload["formula_version"],
        "publication_state": payload["publication_state"],
        "scored_data_fingerprint": payload["scored_data_fingerprint"],
        "comparison_profile_id": payload["comparison_profile_id"],
        "formula": {
            "capability": edition.weights.overall.capability,
            "operational_efficiency": edition.weights.overall.operational_efficiency,
            "access_economics": edition.weights.overall.access_economics,
            "text": (
                "umi_public = 0.55 x Capability + 0.25 x Operational Efficiency "
                "+ 0.20 x Access Economics"
            ),
        },
        "weights": edition.weights.model_dump(mode="json"),
        "limitations": [
            "Access Economics is source-reported public task cost, not provider billing.",
            "95% intervals are unpublished because the extracts are configuration-level means.",
            "This is not v0.3 headline_overall.",
            "Fable is the documented fallback composite product.",
            "DeepSWE cost is diagnostic only (Fable 432/436).",
        ],
        "ranking": ranking,
        "series": series_rows(payload),
        "charts": [
            {
                "id": "umi_public",
                "title": "UMI Public v0.4",
                "type": "bar",
                "y_field": "umi_public",
                "note": "One published number per exact Max configuration.",
            },
            {
                "id": "components",
                "title": "Unweighted component scores",
                "type": "grouped_bar",
                "note": "Each component is 0-100 before overall weights are applied.",
            },
            {
                "id": "contributions",
                "title": "Weighted contributions to umi_public",
                "type": "stacked_bar",
                "note": "Segments are 0.55 Capability, 0.25 Operational Efficiency, 0.20 Access.",
            },
        ],
    }


def _horizontal_bars(
    rows: list[tuple[str, float, str]],
    *,
    title: str,
    max_value: float = 100.0,
    width: int = 760,
) -> str:
    bar_height = 28
    gap = 16
    left = 88
    top = 36
    height = top + len(rows) * (bar_height + gap) + 24
    usable = width - left - 56
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">',
        f'<text x="12" y="20" font-size="14" font-weight="600" fill="#111827">'
        f"{_escape(title)}</text>",
    ]
    for index, (label, value, color) in enumerate(rows):
        y = top + index * (bar_height + gap)
        bar_width = max(0.0, usable * (value / max_value))
        parts.append(
            f'<text x="8" y="{y + 19}" font-size="12" fill="#374151">{_escape(label)}</text>'
        )
        parts.append(
            f'<rect x="{left}" y="{y}" width="{bar_width:.2f}" height="{bar_height}" '
            f'rx="4" fill="{color}"></rect>'
        )
        parts.append(
            f'<text x="{left + bar_width + 8:.2f}" y="{y + 19}" font-size="12" '
            f'fill="#111827">{value:.2f}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _stacked_bars(
    ranking: list[dict[str, Any]],
    *,
    title: str,
    width: int = 760,
) -> str:
    bar_height = 28
    gap = 16
    left = 88
    top = 36
    height = top + len(ranking) * (bar_height + gap) + 48
    usable = width - left - 56
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">',
        f'<text x="12" y="20" font-size="14" font-weight="600" fill="#111827">'
        f"{_escape(title)}</text>",
    ]
    for index, row in enumerate(ranking):
        y = top + index * (bar_height + gap)
        x = float(left)
        segments = (
            ("capability_weighted", COMPONENT_COLORS["capability"]),
            ("operational_efficiency_weighted", COMPONENT_COLORS["operational_efficiency"]),
            ("access_economics_weighted", COMPONENT_COLORS["access_economics"]),
        )
        parts.append(
            f'<text x="8" y="{y + 19}" font-size="12" fill="#374151">'
            f"{_escape(row['short_name'])}</text>"
        )
        for field, color in segments:
            width_px = usable * (float(row[field]) / 100.0)
            parts.append(
                f'<rect x="{x:.2f}" y="{y}" width="{width_px:.2f}" height="{bar_height}" '
                f'fill="{color}"></rect>'
            )
            x += width_px
        parts.append(
            f'<text x="{x + 8:.2f}" y="{y + 19}" font-size="12" fill="#111827">'
            f"{row['umi_public']:.2f}</text>"
        )
    legend_y = height - 18
    legend_x = left
    for label, color in (
        ("Capability x 0.55", COMPONENT_COLORS["capability"]),
        ("Op. Efficiency x 0.25", COMPONENT_COLORS["operational_efficiency"]),
        ("Access x 0.20", COMPONENT_COLORS["access_economics"]),
    ):
        parts.append(
            f'<rect x="{legend_x}" y="{legend_y - 10}" width="10" height="10" '
            f'fill="{color}"></rect>'
        )
        parts.append(
            f'<text x="{legend_x + 14}" y="{legend_y}" font-size="11" fill="#374151">'
            f"{label}</text>"
        )
        legend_x += 170
    parts.append("</svg>")
    return "".join(parts)


def render_public_dashboard_html(dashboard: dict[str, Any]) -> str:
    ranking = dashboard["ranking"]
    public_bars = [
        (row["short_name"], row["umi_public"], COMPONENT_COLORS["umi_public"])
        for row in ranking
    ]
    cap_bars = [
        (row["short_name"], row["capability"], COMPONENT_COLORS["capability"])
        for row in ranking
    ]
    opeff_bars = [
        (
            row["short_name"],
            row["operational_efficiency"],
            COMPONENT_COLORS["operational_efficiency"],
        )
        for row in ranking
    ]
    access_bars = [
        (row["short_name"], row["access_economics"], COMPONENT_COLORS["access_economics"])
        for row in ranking
    ]
    table_rows = "".join(
        (
            "<tr>"
            f"<td>{row['rank']}</td>"
            f"<td>{_escape(row['named_release'])}</td>"
            f"<td>{_escape(row['entity_kind'])}</td>"
            f"<td>{row['capability']:.2f}</td>"
            f"<td>{row['operational_efficiency']:.2f}</td>"
            f"<td>{row['access_economics']:.2f}</td>"
            f"<td><strong>{row['umi_public']:.2f}</strong></td>"
            "<td>unpublished</td>"
            "</tr>"
        )
        for row in ranking
    )
    limitations = "".join(f"<li>{_escape(item)}</li>" for item in dashboard["limitations"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UMI Public v0.4</title>
  <style>
    body {{ font: 15px/1.5 system-ui, sans-serif; margin: 24px auto; max-width: 880px;
           color: #111827; }}
    h1, h2 {{ line-height: 1.2; }}
    .meta, .note {{ color: #4b5563; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px 6px; text-align: left; }}
    th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #6b7280; }}
    svg {{ width: 100%; height: auto; margin: 8px 0 28px; }}
    code {{ font-size: 13px; }}
  </style>
</head>
<body>
  <h1>UMI Public v0.4</h1>
  <p class="meta">{_escape(dashboard["formula"]["text"])}</p>
  <p class="meta">Fingerprint <code>{_escape(dashboard["scored_data_fingerprint"])}</code></p>
  <p class="note">Charts read published <code>model-scores.json</code>.
  They do not recompute scores. Access Economics is source-reported task cost,
  not a provider bill. Intervals are unpublished.</p>
  {_horizontal_bars(public_bars, title="Published UMI Public")}
  {_stacked_bars(ranking, title="Weighted contributions to umi_public")}
  {_horizontal_bars(cap_bars, title="Capability (unweighted)")}
  {_horizontal_bars(opeff_bars, title="Operational Efficiency (unweighted)")}
  {_horizontal_bars(access_bars, title="Access Economics (unweighted)")}
  <h2>Published ranking</h2>
  <table>
    <thead>
      <tr>
        <th>Rank</th><th>Configuration</th><th>Kind</th><th>Capability</th>
        <th>Op. Efficiency</th><th>Access</th><th>UMI Public</th><th>95% interval</th>
      </tr>
    </thead>
    <tbody>{table_rows}</tbody>
  </table>
  <h2>Limitations</h2>
  <ul>{limitations}</ul>
</body>
</html>
"""


def write_chart_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("chart CSV requires rows")
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(handle.getvalue(), encoding="utf-8")


def write_public_dashboard(
    payload: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    dashboard = build_public_dashboard(payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "public-dashboard.json").write_text(
        json.dumps(dashboard, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "public-dashboard.html").write_text(
        render_public_dashboard_html(dashboard), encoding="utf-8"
    )
    write_chart_csv(output_dir / "public-ranking.csv", dashboard["ranking"])
    write_chart_csv(output_dir / "public-series.csv", dashboard["series"])
    return dashboard
