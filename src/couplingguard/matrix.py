from __future__ import annotations

import logging
from collections import defaultdict
from itertools import combinations

from .git_parser import get_file_commit_counts
from .models import Config

log = logging.getLogger(__name__)

CoChangeMatrix = dict[str, dict[str, int]]
NormalizedPair = tuple[float, int, int]  # (score, co_count, max_total_commits)
NormalizedMatrix = dict[tuple[str, str], NormalizedPair]


def build_co_change_matrix(commits: list[list[str]]) -> tuple[CoChangeMatrix, dict[str, int]]:
    """Count per-commit file co-occurrences into a symmetric matrix.

    Returns (co_change, file_counts) where co_change[a][b] == co_change[b][a]
    is the number of commits in which a and b appeared together, and
    file_counts[f] is the total commit count for f over the same window.
    """
    co_change: CoChangeMatrix = defaultdict(lambda: defaultdict(int))
    for files in commits:
        unique_sorted = sorted(set(files))
        for a, b in combinations(unique_sorted, 2):
            co_change[a][b] += 1
            co_change[b][a] += 1

    file_counts = get_file_commit_counts(commits)
    return co_change, file_counts


def filter_by_min_occurrences(
    co_change: CoChangeMatrix, min_occurrences: int
) -> CoChangeMatrix:
    """Drop pairs with co-change count below the threshold. Returns a
    plain dict (no defaultdict semantics) so callers can rely on KeyError
    when looking up a filtered-out file.
    """
    filtered: CoChangeMatrix = {}
    for a, inner in co_change.items():
        kept = {b: c for b, c in inner.items() if c >= min_occurrences}
        if kept:
            filtered[a] = kept
    return filtered


def normalize_pair(co_count: int, count_a: int, count_b: int) -> float:
    """Normalize a raw co-change count into a 0–1 coupling score.

    score = co_count / max(count_a, count_b)
    Returns 0.0 if both totals are zero (defensive; would only happen
    on a degenerate input where co_count > 0 but both files have zero
    commits, which shouldn't be reachable). Rounded to 4 decimals.
    """
    denom = max(count_a, count_b)
    if denom == 0:
        return 0.0
    return round(co_count / denom, 4)


def build_normalized_matrix(
    commits: list[list[str]], config: Config
) -> tuple[NormalizedMatrix, dict[str, int]]:
    """Run the full matrix pipeline: count -> filter -> normalize.

    Returns:
      * matrix: dict keyed by canonical (lo, hi) tuple -> (score, co_count, max_commits)
      * file_counts: per-file total commit count (for the renderer's display)
    """
    co_change, file_counts = build_co_change_matrix(commits)
    co_change = filter_by_min_occurrences(co_change, config.min_occurrences)

    matrix: NormalizedMatrix = {}
    for a, inner in co_change.items():
        for b, co_count in inner.items():
            if a >= b:
                continue
            count_a = file_counts.get(a, 0)
            count_b = file_counts.get(b, 0)
            score = normalize_pair(co_count, count_a, count_b)
            matrix[(a, b)] = (score, co_count, max(count_a, count_b))

    log.debug(
        "build_normalized_matrix: %d pairs after min_occurrences=%d",
        len(matrix),
        config.min_occurrences,
    )
    return matrix, file_counts
