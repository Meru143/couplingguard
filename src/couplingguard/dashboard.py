from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import PRAnalysis

log = logging.getLogger(__name__)

HISTORY_FILE = "coupling-history.json"
DASHBOARD_FILE = "coupling-dashboard.html"
BADGE_FILE = "coupling-score.json"

BADGE_COLORS: dict[str, str] = {
    "low": "brightgreen",
    "medium": "yellow",
    "high": "red",
}

BADGE_MESSAGES: dict[str, str] = {
    "low": "🟢 low",
    "medium": "🟡 medium",
    "high": "🔴 high",
}


def load_history(repo_root: Path) -> list[dict[str, Any]]:
    """Read coupling-history.json from the repo root, returning [] for
    missing or malformed files (per PRD safety guarantee: never crash
    the run because the dashboard file got corrupted).
    """
    path = repo_root / HISTORY_FILE
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.warning(
            "load_history: %s is malformed (%s); starting a fresh history list.",
            path,
            exc,
        )
        return []
    if not isinstance(raw, list):
        log.warning("load_history: %s top-level is not a list; ignoring.", path)
        return []
    return raw


def append_to_history(
    history: list[dict[str, Any]], analysis: PRAnalysis
) -> list[dict[str, Any]]:
    entry: dict[str, Any] = {
        "date": datetime.now(UTC).date().isoformat(),
        "pr": analysis.pr_number,
        "max_score": analysis.max_score,
        "risk": analysis.pr_risk,
        "pair_count": len(analysis.pairs),
    }
    return [*history, entry]


def save_history(history: list[dict[str, Any]], repo_root: Path) -> None:
    path = repo_root / HISTORY_FILE
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    log.debug("save_history: wrote %d entries to %s", len(history), path)


def _last_n(history: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    return history[-n:] if len(history) > n else list(history)


def generate_dashboard_html(history: list[dict[str, Any]]) -> str:
    """Render a static HTML dashboard with an embedded Chart.js line
    chart and a recent-runs table. Returns the full HTML string ready
    to be written to disk (or uploaded as an Actions artifact).
    """
    chart_labels = json.dumps([h.get("date", "") for h in history])
    chart_scores = json.dumps([h.get("max_score", 0.0) for h in history])
    chart_pairs = json.dumps([h.get("pair_count", 0) for h in history])

    recent = list(reversed(_last_n(history, 20)))
    table_rows = "\n".join(
        f"  <tr><td>{h.get('date', '')}</td>"
        f"<td>#{h.get('pr', '')}</td>"
        f"<td>{float(h.get('max_score', 0.0)):.2f}</td>"
        f"<td>{BADGE_MESSAGES.get(str(h.get('risk', 'low')), '⚪')}</td>"
        f"<td>{h.get('pair_count', 0)}</td></tr>"
        for h in recent
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>coupling-dashboard — couplingguard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
h1 {{ font-size: 1.5rem; }}
canvas {{ width: 100%; height: 360px; margin-bottom: 2rem; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 0.4rem 0.6rem; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background: #f4f4f4; }}
</style>
</head>
<body>
<h1>couplingguard — coupling trend</h1>
<canvas id="chart"></canvas>
<table>
<thead><tr><th>Date</th><th>PR</th><th>Max score</th><th>Risk</th><th>Pairs</th></tr></thead>
<tbody>
{table_rows}
</tbody>
</table>
<script>
const ctx = document.getElementById('chart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {chart_labels},
    datasets: [
      {{
        label: 'Max coupling score',
        data: {chart_scores},
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245,158,11,0.15)',
        yAxisID: 'y',
        tension: 0.2,
      }},
      {{
        label: 'Pair count',
        data: {chart_pairs},
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.10)',
        yAxisID: 'y1',
        tension: 0.2,
      }},
    ],
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    stacked: false,
    scales: {{
      y: {{ type: 'linear', display: true, position: 'left', min: 0, max: 1, title: {{ display: true, text: 'Max score' }} }},
      y1: {{ type: 'linear', display: true, position: 'right', min: 0, grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Pair count' }} }},
    }},
  }},
}});
</script>
</body>
</html>
"""


def save_dashboard(html: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / DASHBOARD_FILE
    path.write_text(html, encoding="utf-8")
    log.debug("save_dashboard: wrote %d bytes to %s", len(html), path)
    return path


def save_badge(analysis: PRAnalysis, repo_root: Path) -> Path:
    """Write a shields.io endpoint-badge JSON to the repo root so the
    README badge URL can point at the raw file.

    Format:
    {"schemaVersion": 1, "label": "coupling", "message": "🟢 low", "color": "brightgreen"}
    """
    payload: dict[str, Any] = {
        "schemaVersion": 1,
        "label": "coupling",
        "message": BADGE_MESSAGES.get(analysis.pr_risk, "⚪ unknown"),
        "color": BADGE_COLORS.get(analysis.pr_risk, "lightgrey"),
    }
    path = repo_root / BADGE_FILE
    path.write_text(json.dumps(payload), encoding="utf-8")
    log.debug("save_badge: wrote %s (%s)", path, payload["message"])
    return path
