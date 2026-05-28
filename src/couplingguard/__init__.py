from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from coupling_core import (
    Config as CoreConfig,
)
from coupling_core import (
    build_normalized_matrix,
    get_commits,
    open_repo,
)

from .codeowners_loader import load_codeowners, suggest_reviewers
from .config import load_config
from .dashboard import (
    append_to_history,
    generate_dashboard_html,
    load_history,
    save_badge,
    save_dashboard,
    save_history,
)
from .delta import get_previous_max_score
from .github_poster import (
    check_fail_threshold,
    find_existing_comment,
    get_github_client,
    post_comment,
)
from .gitlab_poster import (
    find_existing_note,
    get_gitlab_client,
    get_mr_iid,
    get_project_id,
    is_gitlab_ci,
    post_mr_note,
)
from .models import (
    Config,
    CouplingGuardError,
    PRAnalysis,
    ShallowCloneError,
)
from .pr_analyzer import analyze_pr, load_pr_files
from .renderer import render_comment, render_info_comment

__version__ = "0.1.1"

log = logging.getLogger("couplingguard")


def _setup_logging() -> None:
    level = logging.DEBUG if os.environ.get("COUPLINGGUARD_DEBUG") == "1" else logging.INFO
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        logging.getLogger().setLevel(level)


def _post_info_comment(reason: str, config: Config, pr_number: int | None) -> None:
    """Post a marker-carrying informational comment, or print to stdout
    when we don't have enough context to reach the PR (no token, no env).
    """
    body = render_info_comment(reason)
    if config.dry_run or pr_number is None:
        print(body)
        return
    try:
        if is_gitlab_ci():
            token = os.environ.get("GITLAB_TOKEN", "")
            if not token:
                print(body)
                return
            gl = get_gitlab_client(token)
            project = gl.projects.get(get_project_id())
            mr = project.mergerequests.get(get_mr_iid())
            post_mr_note(mr, body, dry_run=False)
        else:
            token = os.environ.get("GITHUB_TOKEN", "")
            repo_name = os.environ.get("GITHUB_REPOSITORY", "")
            if not token or not repo_name:
                print(body)
                return
            gh = get_github_client(token)
            repo = gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            post_comment(pr, body, dry_run=False)
    except CouplingGuardError as exc:
        log.warning("Could not post info comment (%s); falling back to stdout.", exc)
        print(body)


def _extract_pr_number_safely() -> int | None:
    """Best-effort PR number extraction without raising; used in the
    error paths where we want to post an info comment but can't risk
    a second exception derailing the cleanup.
    """
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    try:
        import json

        with open(event_path, encoding="utf-8") as fh:
            payload = json.load(fh)
        pr = payload.get("pull_request")
        if isinstance(pr, dict):
            return int(pr["number"])
    except Exception:  # noqa: BLE001
        return None
    return None


def _post_via_platform(
    analysis: PRAnalysis, comment_body: str, config: Config
) -> tuple[int, str | None]:
    """Find any previous comment body (so callers can extract delta), then
    post or edit. Returns (exit_code, previous_body) where exit_code
    is 0 / 1 from the fail_threshold check.
    """
    previous_body: str | None = None

    if config.dry_run:
        print(comment_body)
        if check_fail_threshold(analysis, config):
            return 1, None
        return 0, None

    if is_gitlab_ci():
        token = os.environ.get("GITLAB_TOKEN", "")
        if not token:
            raise CouplingGuardError(
                "couplingguard: Error — GITLAB_TOKEN not set. Cannot post MR note."
            )
        gl = get_gitlab_client(token)
        project = gl.projects.get(get_project_id())
        mr = project.mergerequests.get(get_mr_iid())
        existing = find_existing_note(mr)
        if existing is not None:
            previous_body = getattr(existing, "body", None)
        post_mr_note(mr, comment_body, dry_run=False)
    else:
        token = os.environ.get("GITHUB_TOKEN", "")
        repo_name = os.environ.get("GITHUB_REPOSITORY", "")
        if not token:
            raise CouplingGuardError(
                "couplingguard: Error — GITHUB_TOKEN not set. Cannot post PR comment."
            )
        if not repo_name:
            raise CouplingGuardError(
                "couplingguard: Error — GITHUB_REPOSITORY env var not set."
            )
        gh = get_github_client(token)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(analysis.pr_number)
        existing_comment = find_existing_comment(pr)
        if existing_comment is not None:
            previous_body = getattr(existing_comment, "body", None)
        post_comment(pr, comment_body, dry_run=False)

    exit_code = 1 if check_fail_threshold(analysis, config) else 0
    return exit_code, previous_body


def run(repo_root: Path, action_inputs: dict[str, Any] | None = None) -> int:
    """Top-level entry point. Returns the process exit code.

    The flow is the "railway" pattern: each step either yields a value
    or short-circuits with an informational comment + early return.
    Exceptions are caught at the boundary and mapped to exit codes.
    """
    _setup_logging()
    inputs: dict[str, Any] = action_inputs if action_inputs is not None else {}

    try:
        config = load_config(repo_root, inputs)
    except CouplingGuardError as exc:
        log.error("%s", exc)
        return 1

    try:
        try:
            repo = open_repo(repo_root)
        except ShallowCloneError as exc:
            log.error("%s", exc)
            _post_info_comment(
                "repository is a shallow clone; add 'fetch-depth: 0' to your checkout step.",
                config,
                _extract_pr_number_safely(),
            )
            return 1

        commits = get_commits(repo, config.lookback_days, config.exclude)
        if len(commits) < config.min_occurrences:
            log.warning(
                "couplingguard: Warning — only %d commits in lookback window (need %d).",
                len(commits),
                config.min_occurrences,
            )
            _post_info_comment(
                f"not enough git history (<{config.min_occurrences} commits in lookback window).",
                config,
                _extract_pr_number_safely(),
            )
            return 0

        # coupling_core.build_normalized_matrix takes a coupling_core.Config
        # (subset of couplingguard's Config — no max_pairs/fail_threshold/
        # dry_run/publish_dashboard). Adapt down to just the fields the
        # matrix builder actually consumes.
        core_config = CoreConfig(
            lookback_days=config.lookback_days,
            min_occurrences=config.min_occurrences,
            low_threshold=config.low_threshold,
            high_threshold=config.high_threshold,
            exclude=config.exclude,
        )
        matrix, file_counts = build_normalized_matrix(commits, core_config)

        pr_number, pr_files = load_pr_files(repo)
        if not pr_files:
            _post_info_comment("No changed files detected in this PR.", config, pr_number)
            return 0

        analysis = analyze_pr(pr_number, pr_files, matrix, file_counts, config)

        codeowners = load_codeowners(repo_root)
        suggest_reviewers(analysis.pairs, codeowners, pr_files)

        # First-pass body to look up the previous comment (delta needs it).
        comment_body = render_comment(analysis, config)
        exit_code, previous_body = _post_via_platform(analysis, comment_body, config)

        if previous_body:
            analysis.previous_max_score = get_previous_max_score(previous_body)
            if analysis.previous_max_score is not None:
                # Re-render with the delta line and update the comment
                # in place. One extra render + post is a small price for
                # showing the delta on the first turn after a re-push.
                second_body = render_comment(analysis, config)
                if second_body != comment_body and not config.dry_run:
                    _post_via_platform(analysis, second_body, config)

        if config.publish_dashboard:
            history = load_history(repo_root)
            history = append_to_history(history, analysis)
            save_history(history, repo_root)
            save_dashboard(generate_dashboard_html(history), repo_root)
            save_badge(analysis, repo_root)
            log.info("couplingguard: published dashboard, history, and badge files.")

        return exit_code

    except CouplingGuardError as exc:
        log.error("%s", exc)
        return 1


__all__ = ["__version__", "run", "Config", "PRAnalysis"]


# Convenience for `python -m couplingguard`.
def _main() -> None:
    sys.exit(run(Path("."), {}))
