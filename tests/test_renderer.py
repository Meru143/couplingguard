from __future__ import annotations

import pytest

from couplingguard.delta import extract_previous_data
from couplingguard.models import Config, CouplingPair, PRAnalysis
from couplingguard.renderer import (
    MARKER,
    MAX_BODY_CHARS,
    render_comment,
    render_info_comment,
    render_table_row,
    risk_emoji,
)


@pytest.fixture
def default_config() -> Config:
    return Config(low_threshold=0.3, high_threshold=0.7)


@pytest.fixture
def two_pair_analysis() -> PRAnalysis:
    pairs = [
        CouplingPair(
            "src/payment.py",
            "src/billing.py",
            0.82,
            41,
            50,
            "high",
            suggested_owners=["@alice", "@team-payments"],
        ),
        CouplingPair(
            "src/payment.py",
            "tests/test_billing.py",
            0.64,
            32,
            50,
            "medium",
            suggested_owners=["@alice"],
        ),
    ]
    return PRAnalysis(
        pr_number=142,
        pr_files=["src/payment.py"],
        pairs=pairs,
        max_score=0.82,
        pr_risk="high",
    )


def test_marker_present(two_pair_analysis: PRAnalysis, default_config: Config) -> None:
    body = render_comment(two_pair_analysis, default_config)
    assert MARKER in body


def test_data_blob_round_trips_through_delta_extractor(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    data = extract_previous_data(body)
    assert data is not None
    assert data["max_score"] == 0.82
    assert data["scores"]["src/payment.py"] == 0.82


def test_details_wrapper_present(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    assert "<details>" in body and "</details>" in body


def test_summary_line_has_pair_count_and_emoji(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    assert "2 pairs detected" in body
    assert "🔴 0.82" in body


def test_table_header_present(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    assert "| File in PR | Coupled With | Score | Risk | Co-changes |" in body


def test_table_row_count_matches_pairs(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    rows = [ln for ln in body.splitlines() if ln.startswith("| `src/payment.py")]
    assert len(rows) == 2


def test_delta_line_present_when_previous_score_set(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    two_pair_analysis.previous_max_score = 0.45
    body = render_comment(two_pair_analysis, default_config)
    assert "Score changed since last push" in body
    assert "🟡 0.45 → 🔴 0.82" in body


def test_no_delta_line_when_previous_score_none(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    assert two_pair_analysis.previous_max_score is None
    body = render_comment(two_pair_analysis, default_config)
    assert "Score changed" not in body


def test_no_delta_line_when_score_unchanged(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    two_pair_analysis.previous_max_score = two_pair_analysis.max_score
    body = render_comment(two_pair_analysis, default_config)
    assert "Score changed" not in body


def test_reviewers_line_present_when_owners_set(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    assert "**Suggested reviewers for coupled files:**" in body
    assert "@alice" in body and "@team-payments" in body


def test_reviewers_dedup_in_aggregated_list(
    two_pair_analysis: PRAnalysis, default_config: Config
) -> None:
    body = render_comment(two_pair_analysis, default_config)
    # @alice appears in both pairs' suggested_owners but should be listed once.
    line = [ln for ln in body.splitlines() if "Suggested reviewers" in ln][0]
    assert line.count("@alice") == 1


def test_reviewers_line_absent_when_no_owners(default_config: Config) -> None:
    analysis = PRAnalysis(
        pr_number=1,
        pr_files=["a"],
        pairs=[CouplingPair("a", "b", 0.5, 5, 10, "medium")],
        max_score=0.5,
        pr_risk="medium",
    )
    body = render_comment(analysis, default_config)
    assert "Suggested reviewers" not in body


def test_empty_pairs_shows_info_text(default_config: Config) -> None:
    analysis = PRAnalysis(pr_number=2, pr_files=["x"], pairs=[], max_score=0.0, pr_risk="low")
    body = render_comment(analysis, default_config)
    assert "No coupling patterns detected" in body
    assert MARKER in body
    assert "<details>" not in body


def test_table_row_format() -> None:
    pair = CouplingPair("src/a.py", "src/b.py", 0.82, 41, 50, "high")
    row = render_table_row(pair)
    assert row == "| `src/a.py` | `src/b.py` | 0.82 | 🔴 High | 41/50 commits |"


def test_risk_emoji_known_values() -> None:
    assert risk_emoji("low") == "🟢"
    assert risk_emoji("medium") == "🟡"
    assert risk_emoji("high") == "🔴"


def test_risk_emoji_unknown_value() -> None:
    assert risk_emoji("weird") == "⚪"


def test_truncation_when_body_exceeds_limit(default_config: Config) -> None:
    many = [
        CouplingPair(f"a{i}.py", f"b{i}.py", 0.5, 10, 20, "medium") for i in range(2000)
    ]
    analysis = PRAnalysis(
        pr_number=3, pr_files=["a0.py"], pairs=many, max_score=0.5, pr_risk="medium"
    )
    body = render_comment(analysis, default_config)
    assert len(body) <= MAX_BODY_CHARS
    assert "more pairs" in body


def test_info_comment_format() -> None:
    info = render_info_comment("shallow clone")
    assert MARKER in info
    assert "shallow clone" in info
