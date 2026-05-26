from __future__ import annotations

import json
from pathlib import Path

from couplingguard.dashboard import (
    BADGE_FILE,
    DASHBOARD_FILE,
    HISTORY_FILE,
    append_to_history,
    generate_dashboard_html,
    load_history,
    save_badge,
    save_dashboard,
    save_history,
)
from couplingguard.models import CouplingPair, PRAnalysis


def _make_analysis(pr_number: int = 1, max_score: float = 0.5, risk: str = "medium") -> PRAnalysis:
    pair = CouplingPair("a.py", "b.py", max_score, 5, 10, risk)
    return PRAnalysis(pr_number, ["a.py"], [pair], max_score, risk)


def test_load_history_missing_returns_empty(tmp_path: Path) -> None:
    assert load_history(tmp_path) == []


def test_load_history_malformed_returns_empty(tmp_path: Path) -> None:
    (tmp_path / HISTORY_FILE).write_text("not json {")
    assert load_history(tmp_path) == []


def test_load_history_non_list_returns_empty(tmp_path: Path) -> None:
    (tmp_path / HISTORY_FILE).write_text('{"not": "a list"}')
    assert load_history(tmp_path) == []


def test_new_history_file_created_when_none_exists(tmp_path: Path) -> None:
    history: list[dict] = []
    history = append_to_history(history, _make_analysis(pr_number=1))
    save_history(history, tmp_path)
    loaded = load_history(tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["pr"] == 1


def test_history_append_two_runs(tmp_path: Path) -> None:
    history = append_to_history([], _make_analysis(pr_number=1))
    save_history(history, tmp_path)
    history = append_to_history(load_history(tmp_path), _make_analysis(pr_number=2, max_score=0.8, risk="high"))
    save_history(history, tmp_path)
    final = load_history(tmp_path)
    assert len(final) == 2
    assert final[0]["pr"] == 1 and final[1]["pr"] == 2
    assert final[1]["risk"] == "high"


def test_history_entry_shape() -> None:
    entry = append_to_history([], _make_analysis(pr_number=42, max_score=0.7, risk="medium"))[0]
    assert set(entry.keys()) == {"date", "pr", "max_score", "risk", "pair_count"}
    assert entry["pr"] == 42
    assert entry["pair_count"] == 1


def test_generate_dashboard_html_contains_chartjs_cdn() -> None:
    history = [{"date": "2026-05-26", "pr": 1, "max_score": 0.5, "risk": "medium", "pair_count": 3}]
    html = generate_dashboard_html(history)
    assert "chart.umd" in html or "chart.js" in html.lower()
    assert "cdn.jsdelivr.net" in html


def test_generate_dashboard_html_title() -> None:
    html = generate_dashboard_html([])
    assert "coupling-dashboard" in html


def test_generate_dashboard_html_handles_empty() -> None:
    html = generate_dashboard_html([])
    assert "<table>" in html
    assert "Chart(" in html  # chart still instantiated, just with empty data


def test_save_dashboard_writes_file(tmp_path: Path) -> None:
    html = "<html>test</html>"
    path = save_dashboard(html, tmp_path)
    assert path.name == DASHBOARD_FILE
    assert path.read_text(encoding="utf-8") == html


def test_save_badge_for_high_risk(tmp_path: Path) -> None:
    save_badge(_make_analysis(max_score=0.9, risk="high"), tmp_path)
    badge = json.loads((tmp_path / BADGE_FILE).read_text(encoding="utf-8"))
    assert badge["schemaVersion"] == 1
    assert badge["label"] == "coupling"
    assert badge["color"] == "red"
    assert "high" in badge["message"]


def test_save_badge_for_low_risk(tmp_path: Path) -> None:
    save_badge(_make_analysis(max_score=0.1, risk="low"), tmp_path)
    badge = json.loads((tmp_path / BADGE_FILE).read_text(encoding="utf-8"))
    assert badge["color"] == "brightgreen"


def test_save_badge_for_medium_risk(tmp_path: Path) -> None:
    save_badge(_make_analysis(risk="medium"), tmp_path)
    badge = json.loads((tmp_path / BADGE_FILE).read_text(encoding="utf-8"))
    assert badge["color"] == "yellow"
