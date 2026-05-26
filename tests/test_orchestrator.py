"""Targeted coverage tests for the run() orchestrator and its helpers in
couplingguard/__init__.py.

These tests hit branches that the E2E suite doesn't reach:
* _setup_logging when handlers are already configured
* _post_info_comment fallback paths (no token, no repo env, GitLab branch)
* _extract_pr_number_safely defensive guards
* _post_via_platform GitLab branch
* run() error-catch boundary for ConfigError and CouplingGuardError
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest

from couplingguard import _extract_pr_number_safely, _post_info_comment, _setup_logging, run
from couplingguard.models import Config

# ---------- _setup_logging ---------------------------------------------------


def test_setup_logging_respects_debug_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COUPLINGGUARD_DEBUG", "1")
    # Ensure there's already a handler so we exercise the else-branch
    # (the basicConfig short-circuit).
    root = logging.getLogger()
    placeholder = logging.NullHandler()
    root.addHandler(placeholder)
    try:
        _setup_logging()
        assert root.level == logging.DEBUG
    finally:
        root.removeHandler(placeholder)


def test_setup_logging_default_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COUPLINGGUARD_DEBUG", raising=False)
    root = logging.getLogger()
    placeholder = logging.NullHandler()
    root.addHandler(placeholder)
    try:
        _setup_logging()
        assert root.level == logging.INFO
    finally:
        root.removeHandler(placeholder)


# ---------- _extract_pr_number_safely ---------------------------------------


def test_extract_pr_number_missing_env_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    assert _extract_pr_number_safely() is None


def test_extract_pr_number_unreadable_path_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "nope.json"))
    assert _extract_pr_number_safely() is None


def test_extract_pr_number_malformed_json_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = tmp_path / "event.json"
    bad.write_text("not json {")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(bad))
    assert _extract_pr_number_safely() is None


def test_extract_pr_number_valid_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "event.json"
    p.write_text(json.dumps({"pull_request": {"number": 77}}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(p))
    assert _extract_pr_number_safely() == 77


def test_extract_pr_number_missing_pull_request_key_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "event.json"
    p.write_text(json.dumps({"some_other_event": {}}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(p))
    assert _extract_pr_number_safely() is None


# ---------- _post_info_comment ----------------------------------------------


def test_post_info_comment_dry_run_prints_to_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _post_info_comment("test reason", Config(dry_run=True), pr_number=42)
    out = capsys.readouterr().out
    assert "test reason" in out
    assert "<!-- couplingguard:marker -->" in out


def test_post_info_comment_no_pr_number_falls_back_to_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _post_info_comment("no pr context", Config(), pr_number=None)
    out = capsys.readouterr().out
    assert "no pr context" in out


def test_post_info_comment_no_token_falls_back_to_stdout(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # pr_number is set but token / repo env are not — should fall back.
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    _post_info_comment("token missing", Config(), pr_number=42)
    out = capsys.readouterr().out
    assert "token missing" in out


def test_post_info_comment_gitlab_no_token_falls_back(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CI_SERVER_URL", "https://gitlab.example.com")
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)
    _post_info_comment("gitlab without token", Config(), pr_number=7)
    out = capsys.readouterr().out
    assert "gitlab without token" in out


# ---------- run() error catch boundary --------------------------------------


def test_run_catches_config_error_and_returns_one(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text("invalid: [unclosed\n")
    rc = run(tmp_path, {})
    assert rc == 1


def test_run_catches_generic_couplingguard_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Open_repo on a non-git directory raises CouplingGuardError;
    the top-level catch should map it to exit code 1 cleanly.
    """
    # tmp_path is empty -> not a git repo -> open_repo raises.
    rc = run(tmp_path, {"dry_run": True})
    assert rc == 1


# ---------- _post_via_platform GitLab path ----------------------------------


def test_post_via_platform_gitlab_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When CI_SERVER_URL is set, run() should route through the GitLab
    poster. We mock both gitlab clients so no network is hit.
    """
    monkeypatch.setenv("CI_SERVER_URL", "https://gitlab.example.com")
    monkeypatch.setenv("CI_PROJECT_ID", "1")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")
    monkeypatch.setenv("GITLAB_TOKEN", "fake-token")

    # Build a tiny real repo with enough history.
    repo = git.Repo.init(tmp_path, initial_branch="main")
    with repo.config_writer() as cw:
        cw.set_value("user", "email", "t@t.com")
        cw.set_value("user", "name", "T")
    try:
        for i in range(5):
            f = tmp_path / "a.py"
            f.write_text(f"v{i}")
            g = tmp_path / "b.py"
            g.write_text(f"v{i}")
            repo.index.add(["a.py", "b.py"])
            repo.index.commit(f"c{i}")
        base = repo.head.commit.hexsha
        (tmp_path / "a.py").write_text("pr")
        repo.index.add(["a.py"])
        head_commit = repo.index.commit("PR")
        head = head_commit.hexsha

        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "pull_request": {
                        "number": 7,
                        "base": {"sha": base},
                        "head": {"sha": head},
                    }
                }
            )
        )
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

        # Patch gitlab client constructor so we never hit the network.
        mock_gl = MagicMock()
        mock_project = MagicMock()
        mock_mr = MagicMock()
        mock_mr.notes.list.return_value = []
        mock_gl.projects.get.return_value = mock_project
        mock_project.mergerequests.get.return_value = mock_mr

        with patch("couplingguard.get_gitlab_client", return_value=mock_gl):
            rc = run(tmp_path, {"min_occurrences": 3})

        assert rc == 0
        mock_mr.notes.create.assert_called_once()
        body = mock_mr.notes.create.call_args.args[0]["body"]
        assert "<!-- couplingguard:marker -->" in body
    finally:
        repo.close()


# ---------- run() with publish_dashboard creates artifact files -------------


def test_run_publish_dashboard_writes_score_badge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = git.Repo.init(tmp_path, initial_branch="main")
    with repo.config_writer() as cw:
        cw.set_value("user", "email", "t@t.com")
        cw.set_value("user", "name", "T")
    try:
        for i in range(5):
            (tmp_path / "a.py").write_text(f"v{i}")
            (tmp_path / "b.py").write_text(f"v{i}")
            repo.index.add(["a.py", "b.py"])
            repo.index.commit(f"c{i}")
        base = repo.head.commit.hexsha
        (tmp_path / "a.py").write_text("pr")
        repo.index.add(["a.py"])
        head = repo.index.commit("PR").hexsha

        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {"pull_request": {"number": 1, "base": {"sha": base}, "head": {"sha": head}}}
            )
        )
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

        rc = run(
            tmp_path,
            {"dry_run": True, "publish_dashboard": True, "min_occurrences": 3},
        )
        assert rc == 0

        score = json.loads((tmp_path / "coupling-score.json").read_text(encoding="utf-8"))
        assert score["schemaVersion"] == 1
        assert score["label"] == "coupling"
        assert score["color"] in {"brightgreen", "yellow", "red"}
    finally:
        repo.close()
