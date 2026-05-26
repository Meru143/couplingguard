from __future__ import annotations

import logging
import os
from typing import Any

import gitlab
import gitlab.exceptions

from .github_poster import MARKER, check_fail_threshold
from .models import Config, CouplingGuardError, PRAnalysis

log = logging.getLogger(__name__)


def is_gitlab_ci(env: dict[str, str] | None = None) -> bool:
    """Detect the GitLab CI runtime by the presence of CI_SERVER_URL.

    CI_SERVER_URL is set by every GitLab Runner and is absent from
    GitHub Actions, so it's a clean discriminator.
    """
    src = env if env is not None else os.environ
    return bool(src.get("CI_SERVER_URL"))


def get_mr_iid(env: dict[str, str] | None = None) -> int:
    src = env if env is not None else os.environ
    raw = src.get("CI_MERGE_REQUEST_IID")
    if not raw:
        raise CouplingGuardError(
            "couplingguard: Error — CI_MERGE_REQUEST_IID not set. "
            "This entry point must run on a GitLab merge_request pipeline."
        )
    try:
        return int(raw)
    except ValueError as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — CI_MERGE_REQUEST_IID is not an integer: {raw!r}"
        ) from exc


def get_project_id(env: dict[str, str] | None = None) -> str:
    src = env if env is not None else os.environ
    project_id = src.get("CI_PROJECT_ID")
    if not project_id:
        raise CouplingGuardError(
            "couplingguard: Error — CI_PROJECT_ID not set on the GitLab CI environment."
        )
    return project_id


def get_gitlab_client(token: str, env: dict[str, str] | None = None) -> gitlab.Gitlab:
    if not token:
        raise CouplingGuardError(
            "couplingguard: Error — GITLAB_TOKEN not set. Cannot post MR note."
        )
    src = env if env is not None else os.environ
    server_url = src.get("CI_SERVER_URL")
    if not server_url:
        raise CouplingGuardError(
            "couplingguard: Error — CI_SERVER_URL not set; cannot connect to GitLab."
        )
    gl = gitlab.Gitlab(server_url, private_token=token)
    try:
        gl.auth()
    except gitlab.exceptions.GitlabAuthenticationError as exc:
        raise CouplingGuardError(
            "couplingguard: Error — GitLab authentication failed. "
            "Check that GITLAB_TOKEN has 'api' scope."
        ) from exc
    return gl


def find_existing_note(mr: Any) -> Any | None:
    for note in mr.notes.list(all=True):
        body = getattr(note, "body", "") or ""
        if MARKER in body:
            return note
    return None


def post_mr_note(mr: Any, body: str, dry_run: bool) -> None:
    if dry_run:
        print(body)
        return

    existing = find_existing_note(mr)
    if existing is not None:
        log.info("gitlab_poster: editing existing couplingguard MR note %s.", getattr(existing, "id", "?"))
        existing.body = body
        existing.save()
        return

    log.info("gitlab_poster: creating new couplingguard MR note.")
    mr.notes.create({"body": body})


def run_gitlab_flow(
    analysis: PRAnalysis,
    comment_body: str,
    config: Config,
    token: str,
    client: gitlab.Gitlab | None = None,
) -> int:
    """Orchestrate the GitLab-side post + fail-threshold check.

    Returns 0 on success and 1 when fail_threshold is crossed. The
    `client` kwarg is exposed so tests can inject a mock without
    patching the global gitlab module.
    """
    if config.dry_run:
        print(comment_body)
        if check_fail_threshold(analysis, config):
            return 1
        return 0

    gl = client if client is not None else get_gitlab_client(token)

    try:
        project = gl.projects.get(get_project_id())
        mr = project.mergerequests.get(get_mr_iid())
    except gitlab.exceptions.GitlabAuthenticationError as exc:
        raise CouplingGuardError(
            "couplingguard: Error — GitLab authentication failed while fetching MR."
        ) from exc
    except gitlab.exceptions.GitlabGetError as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — could not load MR (status={exc.response_code}): {exc}"
        ) from exc

    post_mr_note(mr, comment_body, dry_run=False)

    if check_fail_threshold(analysis, config):
        return 1
    return 0
