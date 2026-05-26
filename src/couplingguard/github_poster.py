from __future__ import annotations

import logging
import os
import time
from typing import Any

import github
from github import Auth

from .models import Config, CouplingGuardError, GitHubAuthError, PRAnalysis

log = logging.getLogger(__name__)

MARKER = "<!-- couplingguard:marker -->"

FAIL_THRESHOLD_MINIMUMS: dict[str, float] = {
    "low": 0.0,
    "medium": 0.3,
    "high": 0.7,
}

FAIL_THRESHOLD_LABELS: dict[str, str] = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}

RATE_LIMIT_DEFAULT_SLEEP_SECONDS = 60
RATE_LIMIT_BUFFER_SECONDS = 5


def get_github_client(token: str) -> github.Github:
    if not token:
        raise GitHubAuthError(
            "couplingguard: Error — GitHub token is empty. "
            "Pass `github_token: ${{ github.token }}` to the action."
        )
    return github.Github(auth=Auth.Token(token))


def find_existing_comment(pr: Any) -> Any | None:
    """Walk every issue comment on the PR looking for couplingguard's
    marker. Returns the IssueComment object so the caller can .edit()
    it, or None if no prior comment exists.
    """
    for comment in pr.get_issue_comments():
        body = getattr(comment, "body", "") or ""
        if MARKER in body:
            return comment
    return None


def _sleep_until_rate_limit_reset(exc: github.RateLimitExceededException) -> None:
    reset = None
    headers = getattr(exc, "headers", None)
    if isinstance(headers, dict):
        raw = headers.get("x-ratelimit-reset") or headers.get("X-RateLimit-Reset")
        if raw is not None:
            try:
                reset = int(raw)
            except (TypeError, ValueError):
                reset = None
    if reset is None:
        log.warning(
            "couplingguard: Warning — GitHub API rate limit hit; "
            "no reset timestamp available, sleeping %d seconds.",
            RATE_LIMIT_DEFAULT_SLEEP_SECONDS,
        )
        time.sleep(RATE_LIMIT_DEFAULT_SLEEP_SECONDS)
        return
    delay = max(reset - int(time.time()) + RATE_LIMIT_BUFFER_SECONDS, RATE_LIMIT_BUFFER_SECONDS)
    log.warning(
        "couplingguard: Warning — GitHub API rate limit hit. Retrying after %d seconds (reset=%d).",
        delay,
        reset,
    )
    time.sleep(delay)


def _post_or_edit(pr: Any, body: str) -> None:
    existing = find_existing_comment(pr)
    if existing is not None:
        log.info("github_poster: editing existing couplingguard comment %s.", getattr(existing, "id", "?"))
        existing.edit(body)
    else:
        log.info("github_poster: creating new couplingguard comment on PR #%s.", getattr(pr, "number", "?"))
        pr.create_issue_comment(body)


def post_comment(pr: Any, body: str, dry_run: bool) -> None:
    """Post or edit the PR comment, with one rate-limit retry and an
    explicit auth-error mapping for 403 responses.
    """
    if dry_run:
        print(body)
        return

    attempts = 0
    while True:
        attempts += 1
        try:
            _post_or_edit(pr, body)
            return
        except github.RateLimitExceededException as exc:
            if attempts > 1:
                log.error("github_poster: still rate-limited after retry; giving up.")
                raise
            _sleep_until_rate_limit_reset(exc)
        except github.GithubException as exc:
            if exc.status == 403:
                raise GitHubAuthError(
                    "couplingguard: Error — could not post PR comment. "
                    "Verify 'permissions: pull-requests: write' is set."
                ) from exc
            raise CouplingGuardError(
                f"couplingguard: Error — GitHub API call failed (status={exc.status}): {exc}"
            ) from exc


def check_fail_threshold(analysis: PRAnalysis, config: Config) -> bool:
    """Return True iff the analysis's max_score crosses the configured
    fail threshold. Logs the exact PRD section 10 E007 message before
    returning True so the failure reason is visible in the Actions log.
    """
    if config.fail_threshold is None:
        return False
    if config.fail_threshold not in FAIL_THRESHOLD_MINIMUMS:
        raise CouplingGuardError(
            f"couplingguard: Error — invalid fail_threshold {config.fail_threshold!r}; "
            "expected 'low', 'medium', or 'high'."
        )
    minimum = FAIL_THRESHOLD_MINIMUMS[config.fail_threshold]
    if analysis.max_score >= minimum and analysis.pairs:
        label = FAIL_THRESHOLD_LABELS[config.fail_threshold]
        log.error(
            "couplingguard: PR coupling density %.2f exceeds fail_threshold=%s (%.2f). Failing check.",
            analysis.max_score,
            label.lower(),
            minimum,
        )
        return True
    return False


def run_github_flow(
    analysis: PRAnalysis,
    comment_body: str,
    config: Config,
    token: str,
    client: github.Github | None = None,
) -> int:
    """Orchestrate the GitHub-side post + fail-threshold check.

    Returns the process exit code: 0 on success, 1 when fail_threshold
    is set and the PR coupling density crosses it. The `client` kwarg
    is exposed so tests can inject a mock.
    """
    if config.dry_run:
        print(comment_body)
        if check_fail_threshold(analysis, config):
            return 1
        return 0

    gh = client if client is not None else get_github_client(token)

    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_name:
        raise CouplingGuardError(
            "couplingguard: Error — GITHUB_REPOSITORY env var not set. "
            "This entry point must be invoked from a GitHub Actions workflow."
        )

    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(analysis.pr_number)
    except github.GithubException as exc:
        if exc.status in (401, 403):
            raise GitHubAuthError(
                "couplingguard: Error — could not access PR. "
                "Verify the github_token has 'pull-requests: write' permission."
            ) from exc
        raise CouplingGuardError(
            f"couplingguard: Error — could not load PR #{analysis.pr_number} "
            f"from {repo_name} (status={exc.status}): {exc}"
        ) from exc

    post_comment(pr, comment_body, dry_run=False)

    if check_fail_threshold(analysis, config):
        return 1
    return 0
