from __future__ import annotations

import json
import logging
import os
from typing import Any

import git

from .matrix import NormalizedMatrix
from .models import Config, CouplingGuardError, CouplingPair, PRAnalysis

log = logging.getLogger(__name__)

MAX_PR_FILES = 200


def _load_event_payload(event_path: str | None = None) -> dict[str, Any]:
    path = event_path or os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        raise CouplingGuardError(
            "couplingguard: Error — GITHUB_EVENT_PATH not set. "
            "This entry point must be invoked from a GitHub Actions PR workflow."
        )
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — GITHUB_EVENT_PATH {path!r} does not exist."
        ) from exc
    except json.JSONDecodeError as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — GITHUB_EVENT_PATH JSON is malformed: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CouplingGuardError(
            "couplingguard: Error — GITHUB_EVENT_PATH payload is not an object."
        )
    return payload


def _extract_pr_metadata(event: dict[str, Any]) -> tuple[int, str, str]:
    """Pull PR number, base SHA, head SHA from a pull_request event payload."""
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        raise CouplingGuardError(
            "couplingguard: Error — event payload is missing the 'pull_request' object."
        )
    try:
        number = int(pr["number"])
        base_sha = str(pr["base"]["sha"])
        head_sha = str(pr["head"]["sha"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — event payload missing pull_request.number/base.sha/head.sha: {exc}"
        ) from exc
    return number, base_sha, head_sha


def _diff_files(repo: git.Repo, base_sha: str, head_sha: str) -> list[str]:
    raw = repo.git.diff("--name-only", f"{base_sha}...{head_sha}")
    return [line for line in raw.splitlines() if line.strip()]


def load_pr_files(
    repo: git.Repo, event_path: str | None = None
) -> tuple[int, list[str]]:
    """Load (pr_number, pr_files) from the Actions event payload + a local diff.

    Uses the three-dot triple-diff (base...head) so the file list matches
    what GitHub itself shows on the PR diff page. Caps the list at
    MAX_PR_FILES (200) per PRD edge case 6, logging a warning so the
    user knows truncation happened.
    """
    event = _load_event_payload(event_path)
    pr_number, base_sha, head_sha = _extract_pr_metadata(event)

    try:
        files = _diff_files(repo, base_sha, head_sha)
    except git.exc.GitCommandError as exc:
        log.warning(
            "load_pr_files: git diff %s...%s failed (%s); returning empty file list",
            base_sha,
            head_sha,
            exc,
        )
        return pr_number, []

    if len(files) > MAX_PR_FILES:
        log.warning(
            "load_pr_files: PR has %d changed files; truncating to %d for analysis.",
            len(files),
            MAX_PR_FILES,
        )
        files = files[:MAX_PR_FILES]

    if not files:
        log.info("load_pr_files: PR #%d has no changed files in diff.", pr_number)

    return pr_number, files


def classify_risk(score: float, config: Config) -> str:
    if score < config.low_threshold:
        return "low"
    if score < config.high_threshold:
        return "medium"
    return "high"


def find_coupling_pairs(
    pr_files: list[str],
    matrix: NormalizedMatrix,
    file_counts: dict[str, int],
    config: Config,
) -> list[CouplingPair]:
    """Filter the global matrix down to pairs involving the PR's files.

    Iterates the canonical-keyed matrix once and emits one CouplingPair
    per pair where either side is in pr_files. The PR-side file is
    placed in `file_in_pr`; the other in `coupled_file`. If both sides
    are in the PR (which is normal for a coordinated change), the
    alphabetically-first one is reported as the PR file so the same
    pair is never emitted twice.
    """
    del file_counts  # captured in matrix tuple already; kept in signature per PRD section 9
    pr_set = set(pr_files)
    if not pr_set:
        return []

    pairs: list[CouplingPair] = []
    for (a, b), (score, co_count, total) in matrix.items():
        a_in = a in pr_set
        b_in = b in pr_set
        if not (a_in or b_in):
            continue
        if a_in:
            file_in_pr, coupled = a, b
        else:
            file_in_pr, coupled = b, a
        pairs.append(
            CouplingPair(
                file_in_pr=file_in_pr,
                coupled_file=coupled,
                score=score,
                co_changes=co_count,
                total_commits=total,
                risk=classify_risk(score, config),
            )
        )

    pairs.sort(key=lambda p: p.score, reverse=True)
    return pairs[: config.max_pairs]


def analyze_pr(
    pr_number: int,
    pr_files: list[str],
    matrix: NormalizedMatrix,
    file_counts: dict[str, int],
    config: Config,
) -> PRAnalysis:
    pairs = find_coupling_pairs(pr_files, matrix, file_counts, config)
    max_score = max((p.score for p in pairs), default=0.0)
    pr_risk = classify_risk(max_score, config) if pairs else "low"
    return PRAnalysis(
        pr_number=pr_number,
        pr_files=pr_files,
        pairs=pairs,
        max_score=max_score,
        pr_risk=pr_risk,
    )


# Re-exports kept on the public surface so other modules (and tests)
# don't reach into the private helpers.
__all__ = [
    "MAX_PR_FILES",
    "analyze_pr",
    "classify_risk",
    "find_coupling_pairs",
    "load_pr_files",
]
