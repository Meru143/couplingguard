from __future__ import annotations

from couplingguard.matrix import (
    build_co_change_matrix,
    build_normalized_matrix,
    filter_by_min_occurrences,
    normalize_pair,
)
from couplingguard.models import Config


def test_two_files_one_commit_count_is_one() -> None:
    co, _ = build_co_change_matrix([["a.py", "b.py"]])
    assert co["a.py"]["b.py"] == 1
    assert co["b.py"]["a.py"] == 1


def test_two_files_five_commits_count_is_five() -> None:
    commits = [["a.py", "b.py"]] * 5
    co, counts = build_co_change_matrix(commits)
    assert co["a.py"]["b.py"] == 5
    assert counts["a.py"] == 5
    assert counts["b.py"] == 5


def test_three_file_commit_produces_three_pairs() -> None:
    co, _ = build_co_change_matrix([["a", "b", "c"]])
    assert co["a"]["b"] == 1
    assert co["a"]["c"] == 1
    assert co["b"]["c"] == 1


def test_normalize_pair_formula() -> None:
    # PRD section 6.1: score = co_count / max(count_a, count_b)
    assert normalize_pair(10, 10, 20) == 0.5
    assert normalize_pair(5, 8, 5) == 0.625
    assert normalize_pair(0, 5, 5) == 0.0


def test_normalize_pair_zero_denominator_is_zero() -> None:
    assert normalize_pair(0, 0, 0) == 0.0


def test_normalize_pair_rounded_to_four_decimals() -> None:
    # 1/3 = 0.33333... -> 0.3333 (4 dp)
    score = normalize_pair(1, 3, 2)
    assert score == 0.3333


def test_filter_by_min_occurrences_drops_low_pairs() -> None:
    commits = [["a", "b"]] * 5 + [["a", "c"]] * 2
    co, _ = build_co_change_matrix(commits)
    filtered = filter_by_min_occurrences(co, min_occurrences=3)
    assert "b" in filtered.get("a", {})
    assert "c" not in filtered.get("a", {})


def test_pair_at_min_occurrences_kept() -> None:
    co, _ = build_co_change_matrix([["a", "b"]] * 3)
    filtered = filter_by_min_occurrences(co, min_occurrences=3)
    assert filtered["a"]["b"] == 3


def test_empty_commits_returns_empty_matrix() -> None:
    co, counts = build_co_change_matrix([])
    assert dict(co) == {}
    assert counts == {}


def test_build_normalized_matrix_canonical_keys() -> None:
    commits = [["a", "b"]] * 5
    matrix, counts = build_normalized_matrix(commits, Config(min_occurrences=3))
    # Canonical (lo, hi) ordering: only ('a', 'b') in keys, not ('b', 'a').
    assert ("a", "b") in matrix
    assert ("b", "a") not in matrix
    score, co_count, max_total = matrix[("a", "b")]
    assert score == 1.0 and co_count == 5 and max_total == 5
    assert counts["a"] == 5 and counts["b"] == 5


def test_build_normalized_matrix_empty() -> None:
    matrix, counts = build_normalized_matrix([], Config())
    assert matrix == {}
    assert counts == {}


def test_normalization_correct_for_different_totals() -> None:
    # a appears in 10 commits (5 with b, 5 alone), b only in 5.
    commits = [["a", "b"]] * 5 + [["a"]] * 5
    matrix, _ = build_normalized_matrix(commits, Config(min_occurrences=3))
    score, co_count, max_total = matrix[("a", "b")]
    assert co_count == 5
    assert max_total == 10
    assert score == 0.5  # 5 / max(10, 5)
