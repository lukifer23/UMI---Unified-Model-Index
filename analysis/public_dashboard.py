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
    "gemini-3.6-flash-high": "Gemini 3.6 Flash",
    "gpt-5.4-2026-03-05-xhigh": "GPT-5.4",
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
CAPABILITY_SERIES_ORDER = (
    "epoch-chess-puzzles",
    "deepswe-v1.1-pass1",
    "epoch-scicode",
    "epoch-weirdml",
    "epoch-gpqa",
    "epoch-otis-aime",
    "epoch-critpt",
)


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
                "short_name": SHORT_NAMES.get(item["entity_id"], item["named_release"]),
                "capability": _round(capability),
                "operational_efficiency": _round(opeff),
                "access_economics": _round(access),
                "umi_public": _round(public),
                "capability_weighted": _round(weights.capability * capability),
                "operational_efficiency_weighted": _round(
                    weights.operational_efficiency * opeff
                ),
                "access_economics_weighted": _round(weights.access_economics * access),
                "interval_low": None,
                "interval_high": None,
                "rank_low": item["rank"],
                "rank_high": item["rank"],
                "interval_status": "unpublished_point_extracts",
                "indistinguishable_from": (),
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
                        "short_name": SHORT_NAMES.get(item["entity_id"], item["named_release"]),
                        "component": component,
                        "series_id": series_id,
                        "series_label": SERIES_LABELS.get(series_id, series_id),
                        "raw": _round(detail["raw"]),
                        "score": _round(detail["score"]),
                    }
                )
    return rows


def attach_public_sidecars(payload: dict[str, Any], processed_dir: Path) -> dict[str, Any]:
    attached = dict(payload)
    for name in ("uncertainty", "validation", "certificate"):
        path = processed_dir / f"{name}.json"
        if name == "certificate":
            path = processed_dir / "public-index-certificate.json"
        if name in attached or not path.is_file():
            continue
        attached[name] = json.loads(path.read_text(encoding="utf-8"))
    return attached


def build_public_dashboard(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "published",
        "experimental_point_score",
        "historical_experimental_point_score",
        "provisional_public_score",
        "certified_public_score",
    }
    if payload.get("publication_state") not in allowed:
        raise ValueError("public dashboard requires a documented public publication_state")
    models = payload["models"]
    if any(item.get("umi_public") is None for item in models):
        raise ValueError("public dashboard refuses to plot a null umi_public as zero")
    edition_name = "v0.5" if str(payload.get("edition_id", "")).endswith("v0.5") else "v0.4"
    edition = load_public_edition_config(edition=edition_name)
    ranking = chart_rows(payload)
    uncertainty_models = payload.get("uncertainty", {}).get("models", ())
    if uncertainty_models:
        from umi.public_certificate import overlapping_pairs

        by_id = {item["entity_id"]: item for item in uncertainty_models}
        for row in ranking:
            interval = by_id.get(row["entity_id"])
            if interval is None:
                continue
            row["interval_low"] = _round(interval["interval_low"])
            row["interval_high"] = _round(interval["interval_high"])
            row["rank_low"] = interval["rank_low"]
            row["rank_high"] = interval["rank_high"]
            row["interval_status"] = interval["interval_status"]
        pairs = overlapping_pairs(ranking)
        neighbors: dict[str, list[str]] = {row["entity_id"]: [] for row in ranking}
        for left, right in pairs:
            neighbors[left].append(right)
            neighbors[right].append(left)
        for row in ranking:
            row["indistinguishable_from"] = tuple(sorted(neighbors[row["entity_id"]]))
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
        "limitations": _dashboard_limitations(bool(uncertainty_models)),
        "ranking": ranking,
        "series": series_rows(payload),
        "charts": [
            {
                "id": "umi_public",
                "title": "UMI Public",
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
            {
                "id": "capability_heatmap",
                "title": "Capability series scores",
                "type": "heatmap",
                "note": "0-100 robust-z scores from the frozen common-core extracts.",
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


def _grouped_component_bars(
    ranking: list[dict[str, Any]],
    *,
    title: str,
    width: int = 760,
) -> str:
    left = 40
    top = 36
    bottom = 56
    plot_height = 220
    height = top + plot_height + bottom
    usable = width - left - 24
    group_width = usable / max(len(ranking), 1)
    bar_width = group_width / 5
    fields = (
        ("capability", COMPONENT_COLORS["capability"], "Capability"),
        ("operational_efficiency", COMPONENT_COLORS["operational_efficiency"], "Op. Eff."),
        ("access_economics", COMPONENT_COLORS["access_economics"], "Access"),
    )
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">',
        f'<text x="12" y="20" font-size="14" font-weight="600" fill="#111827">'
        f"{_escape(title)}</text>",
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" '
        f'stroke="#d1d5db"></line>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{width - 16}" '
        f'y2="{top + plot_height}" stroke="#d1d5db"></line>',
    ]
    for index, row in enumerate(ranking):
        group_x = left + index * group_width + bar_width
        for offset, (field, color, _label) in enumerate(fields):
            value = float(row[field])
            bar_h = plot_height * (value / 100.0)
            x = group_x + offset * bar_width
            y = top + plot_height - bar_h
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 3:.2f}" '
                f'height="{bar_h:.2f}" fill="{color}"></rect>'
            )
        parts.append(
            f'<text x="{left + index * group_width + group_width / 2:.2f}" '
            f'y="{top + plot_height + 18}" font-size="12" text-anchor="middle" '
            f'fill="#374151">{_escape(row["short_name"])}</text>'
        )
    legend_y = height - 14
    legend_x = left
    for _field, color, label in fields:
        parts.append(
            f'<rect x="{legend_x}" y="{legend_y - 10}" width="10" height="10" '
            f'fill="{color}"></rect>'
        )
        parts.append(
            f'<text x="{legend_x + 14}" y="{legend_y}" font-size="11" fill="#374151">'
            f"{label}</text>"
        )
        legend_x += 120
    parts.append("</svg>")
    return "".join(parts)


def _score_fill(score: float) -> tuple[str, str]:
    ratio = min(max(score / 100.0, 0.0), 1.0)
    red = int(241 + (29 - 241) * ratio)
    green = int(245 + (78 - 245) * ratio)
    blue = int(249 + (216 - 249) * ratio)
    ink = "#111827" if score < 58 else "#ffffff"
    return f"rgb({red},{green},{blue})", ink


def _capability_heatmap(
    ranking: list[dict[str, Any]],
    series: list[dict[str, Any]],
    *,
    title: str,
    width: int = 760,
) -> str:
    models = [row["short_name"] for row in ranking]
    lookup = {
        (row["short_name"], row["series_id"]): float(row["score"])
        for row in series
        if row["component"] == "capability"
    }
    left = 108
    top = 48
    cell_w = (width - left - 16) / max(len(models), 1)
    cell_h = 28
    height = top + len(CAPABILITY_SERIES_ORDER) * cell_h + 28
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">',
        f'<text x="12" y="20" font-size="14" font-weight="600" fill="#111827">'
        f"{_escape(title)}</text>",
    ]
    for column, name in enumerate(models):
        parts.append(
            f'<text x="{left + column * cell_w + cell_w / 2:.2f}" y="{top - 8}" '
            f'font-size="12" text-anchor="middle" fill="#374151">{_escape(name)}</text>'
        )
    for row_index, series_id in enumerate(CAPABILITY_SERIES_ORDER):
        y = top + row_index * cell_h
        parts.append(
            f'<text x="8" y="{y + 19}" font-size="11" fill="#374151">'
            f"{_escape(SERIES_LABELS[series_id])}</text>"
        )
        for column, name in enumerate(models):
            score = lookup[(name, series_id)]
            fill, ink = _score_fill(score)
            x = left + column * cell_w
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_w - 2:.2f}" '
                f'height="{cell_h - 2:.2f}" fill="{fill}"></rect>'
            )
            parts.append(
                f'<text x="{x + cell_w / 2:.2f}" y="{y + 18:.2f}" font-size="11" '
                f'text-anchor="middle" fill="{ink}">{score:.1f}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _interval_cell(row: dict[str, Any]) -> str:
    if row.get("interval_low") is None or row.get("interval_high") is None:
        return "unpublished"
    cluster = row.get("indistinguishable_from") or ()
    note = f" overlaps {len(cluster)}" if cluster else " distinct"
    return (
        f"{row['interval_low']:.2f}–{row['interval_high']:.2f} "
        f"(ranks {row['rank_low']}–{row['rank_high']}){note}"
    )


def render_public_dashboard_html(dashboard: dict[str, Any]) -> str:
    ranking = dashboard["ranking"]
    public_bars = [
        (row["short_name"], row["umi_public"], COMPONENT_COLORS["umi_public"])
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
            f"<td>{_interval_cell(row)}</td>"
            "</tr>"
        )
        for row in ranking
    )
    limitations = "".join(f"<li>{_escape(item)}</li>" for item in dashboard["limitations"])
    weights = dashboard["weights"]
    series_header = "".join(
        f"<th>{_escape(SERIES_LABELS[series_id])}</th>" for series_id in CAPABILITY_SERIES_ORDER
    )
    series_lookup = {
        (row["short_name"], row["series_id"]): row["score"]
        for row in dashboard["series"]
        if row["component"] == "capability"
    }
    series_body = "".join(
        "<tr>"
        + f"<td>{_escape(row['short_name'])}</td>"
        + "".join(
            f"<td>{series_lookup[(row['short_name'], series_id)]:.1f}</td>"
            for series_id in CAPABILITY_SERIES_ORDER
        )
        + "</tr>"
        for row in ranking
    )
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
  not a provider bill. Partial intervals are shown when published; overlapping
  intervals are not a unique rank.</p>
  {_horizontal_bars(public_bars, title="Published UMI Public")}
  {_stacked_bars(ranking, title="Weighted contributions to umi_public")}
  {_grouped_component_bars(ranking, title="Unweighted components")}
  {_capability_heatmap(ranking, dashboard["series"], title="Capability series scores")}
  <h2>Methods</h2>
  <p class="note">Capability domains: general reasoning
  {weights["capability_domains"]["general_reasoning_and_knowledge"]:.2f},
  software {weights["capability_domains"]["software_engineering"]:.2f},
  agentic {weights["capability_domains"]["agentic_and_tool_mediated_work"]:.2f},
  math/science {weights["capability_domains"]["mathematics_and_science"]:.2f}.
  Operational Efficiency is DeepSWE tokens
  {weights["operational_efficiency"]["task_resource_intensity"]:.2f} and steps
  {weights["operational_efficiency"]["task_completion_time_and_steps"]:.2f}.
  Access is WeirdML high-effort cost
  {weights["access_economics"]["public_benchmark_task_cost"]:.2f}.</p>
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
  <h2>Capability series</h2>
  <table>
    <thead>
      <tr><th>Model</th>{series_header}</tr>
    </thead>
    <tbody>{series_body}</tbody>
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
    flattened = []
    for row in rows:
        item = dict(row)
        for key, value in item.items():
            if isinstance(value, tuple):
                item[key] = "|".join(str(part) for part in value)
        flattened.append(item)
    writer.writerows(flattened)
    path.write_text(handle.getvalue(), encoding="utf-8")


def _dashboard_limitations(has_intervals: bool) -> list[str]:
    interval_note = (
        "Partial source-interval ranks overlap for some models and are not a unique order."
        if has_intervals
        else "95% intervals are unpublished because this payload has no uncertainty sidecar."
    )
    return [
        "Access Economics is source-reported public task cost, not provider billing.",
        "Operational Efficiency is source-reported DeepSWE means, not success-adjusted resources.",
        interval_note,
        "This is not v0.3 headline_overall.",
        "Fable is the documented fallback composite product.",
        "DeepSWE cost is diagnostic only (Fable 432/436).",
    ]


def write_public_dashboard(
    payload: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    dashboard = build_public_dashboard(attach_public_sidecars(payload, output_dir))
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
