from __future__ import annotations

import pytest

from couplingguard.models import Config
from couplingguard.pr_analyzer import (
    MAX_PR_FILES,
    analyze_pr,
    classify_risk,
    find_coupling_pairs,
)


@pytest.fixture
def default_config() -> Config:
    return Config(low_threshold=0.3, high_threshold=0.7, max_pairs=10)


def test_classify_risk_below_low_is_low(default_config: Config) -> None:
    assert classify_risk(0.29, default_config) == "low"


def test_classify_risk_at_low_boundary_is_medium(default_config: Config) -> None:
    # 0.30 is the start of "medium" — strict >= rule
    assert classify_risk(0.30, default_config) == "medium"


def test_classify_risk_just_below_high_is_medium(default_config: Config) -> None:
    assert classify_risk(0.699, default_config) == "medium"


def test_classify_risk_at_high_boundary_is_high(default_config: Config) -> None:
    assert classify_risk(0.70, default_config) == "high"


def test_only_pairs_with_pr_files_returned(default_config: Config) -> None:
    matrix = {
        ("a.py", "b.py"): (0.8, 10, 12),
        ("c.py", "d.py"): (0.6, 6, 10),  # neither in PR
    }
    pairs = find_coupling_pairs(["a.py"], matrix, {}, default_config)
    assert len(pairs) == 1
    assert pairs[0].file_in_pr == "a.py"
    assert pairs[0].coupled_file == "b.py"


def test_pairs_sorted_by_score_descending(default_config: Config) -> None:
    matrix = {
        ("a.py", "low.py"): (0.2, 2, 10),
        ("a.py", "high.py"): (0.9, 9, 10),
        ("a.py", "mid.py"): (0.5, 5, 10),
    }
    pairs = find_coupling_pairs(["a.py"], matrix, {}, default_config)
    assert [p.score for p in pairs] == [0.9, 0.5, 0.2]


def test_max_pairs_truncates() -> None:
    cfg = Config(max_pairs=2)
    matrix = {("a", f"b{i}"): (0.9 - i * 0.1, 9, 10) for i in range(5)}
    pairs = find_coupling_pairs(["a"], matrix, {}, cfg)
    assert len(pairs) == 2


def test_file_in_pr_flips_when_pair_is_other_pr(default_config: Config) -> None:
    # Matrix has canonical (a, b) but the PR contains b — file_in_pr must be b.
    matrix = {("a.py", "b.py"): (0.8, 10, 12)}
    pairs = find_coupling_pairs(["b.py"], matrix, {}, default_config)
    assert pairs[0].file_in_pr == "b.py"
    assert pairs[0].coupled_file == "a.py"


def test_empty_pr_files_returns_empty(default_config: Config) -> None:
    matrix = {("a", "b"): (0.5, 5, 10)}
    assert find_coupling_pairs([], matrix, {}, default_config) == []


def test_analyze_pr_max_score_and_risk(default_config: Config) -> None:
    matrix = {
        ("a.py", "b.py"): (0.82, 10, 12),
        ("a.py", "c.py"): (0.45, 5, 11),
    }
    analysis = analyze_pr(42, ["a.py"], matrix, {}, default_config)
    assert analysis.pr_number == 42
    assert analysis.max_score == 0.82
    assert analysis.pr_risk == "high"
    assert len(analysis.pairs) == 2


def test_analyze_pr_no_pairs_is_low_risk_zero_score(default_config: Config) -> None:
    analysis = analyze_pr(1, ["z.py"], {}, {}, default_config)
    assert analysis.pairs == []
    assert analysis.max_score == 0.0
    assert analysis.pr_risk == "low"


def test_co_changes_and_total_commits_propagated(default_config: Config) -> None:
    matrix = {("a", "b"): (0.5, 7, 14)}
    pair = find_coupling_pairs(["a"], matrix, {}, default_config)[0]
    assert pair.co_changes == 7
    assert pair.total_commits == 14


def test_max_pr_files_constant_is_two_hundred() -> None:
    # PRD edge case 6.
    assert MAX_PR_FILES == 200
