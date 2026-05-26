from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import git
import pytest


@pytest.fixture
def fake_repo(tmp_path: Path) -> Iterator[git.Repo]:
    """Initialize a real on-disk git repo at tmp_path.

    Uses repo.close() at teardown so GitPython releases its file
    handles before pytest cleans up the tempdir — without this,
    Windows hits 'access denied' errors at the end of every test.
    """
    repo = git.Repo.init(tmp_path, initial_branch="main")
    with repo.config_writer() as cw:
        cw.set_value("user", "email", "test@example.com")
        cw.set_value("user", "name", "Test")
    try:
        yield repo
    finally:
        repo.close()


@pytest.fixture
def commit_files(
    fake_repo: git.Repo, tmp_path: Path
) -> Callable[[list[str], str], git.Commit]:
    """Return a helper that writes files and creates a commit in fake_repo."""

    def _do(files: list[str], message: str = "test commit") -> git.Commit:
        for f in files:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            # Use a unique payload each call so subsequent commits aren't no-ops.
            existing = p.read_text(encoding="utf-8") if p.exists() else ""
            p.write_text(existing + f"\n{f}-{message}", encoding="utf-8")
        fake_repo.index.add(files)
        return fake_repo.index.commit(message)

    return _do


@pytest.fixture
def fake_pr_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., Path]:
    """Return a builder that writes a GitHub pull_request event payload
    to a temp file and sets GITHUB_EVENT_PATH to it.
    """

    def _build(number: int = 1, base_sha: str = "BASE", head_sha: str = "HEAD") -> Path:
        payload: dict[str, Any] = {
            "pull_request": {
                "number": number,
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            }
        }
        path = tmp_path / "event.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
        return path

    return _build


@pytest.fixture
def mock_github() -> MagicMock:
    """A MagicMock pre-shaped like a PyGithub Github client.

    Tests can attach their own return values to:
      mock_github.get_repo.return_value
      mock_github.get_repo.return_value.get_pull.return_value
      mock_github.get_repo.return_value.get_pull.return_value.get_issue_comments.return_value
    """
    client = MagicMock()
    repo = MagicMock()
    pr = MagicMock()
    pr.get_issue_comments.return_value = []
    repo.get_pull.return_value = pr
    client.get_repo.return_value = repo
    return client


@pytest.fixture(autouse=True)
def _clear_couplingguard_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no GitHub / GitLab env vars leak between tests."""
    for key in (
        "GITHUB_TOKEN",
        "GITHUB_REPOSITORY",
        "GITHUB_EVENT_PATH",
        "GITLAB_TOKEN",
        "CI_SERVER_URL",
        "CI_PROJECT_ID",
        "CI_MERGE_REQUEST_IID",
        "COUPLINGGUARD_DEBUG",
    ):
        monkeypatch.delenv(key, raising=False)
    # Also clear any INPUT_* leftovers from previous runs.
    import os

    for key in list(os.environ):
        if key.startswith("INPUT_"):
            monkeypatch.delenv(key, raising=False)
