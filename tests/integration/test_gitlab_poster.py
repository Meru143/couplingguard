from __future__ import annotations

from unittest.mock import MagicMock

import gitlab.exceptions
import pytest

from couplingguard.github_poster import MARKER
from couplingguard.gitlab_poster import (
    find_existing_note,
    get_mr_iid,
    get_project_id,
    is_gitlab_ci,
    post_mr_note,
    run_gitlab_flow,
)
from couplingguard.models import (
    Config,
    CouplingGuardError,
    CouplingPair,
    PRAnalysis,
)


def _mk_analysis(score: float = 0.5, risk: str = "medium") -> PRAnalysis:
    return PRAnalysis(
        pr_number=7,
        pr_files=["a.py"],
        pairs=[CouplingPair("a.py", "b.py", score, 5, 10, risk)],
        max_score=score,
        pr_risk=risk,
    )


def _mk_mr_no_existing() -> MagicMock:
    mr = MagicMock()
    mr.notes.list.return_value = []
    return mr


def test_is_gitlab_ci_detects_env() -> None:
    assert is_gitlab_ci({}) is False
    assert is_gitlab_ci({"CI_SERVER_URL": "https://gitlab.com"}) is True


def test_get_mr_iid_valid() -> None:
    assert get_mr_iid({"CI_MERGE_REQUEST_IID": "42"}) == 42


def test_get_mr_iid_missing_raises() -> None:
    with pytest.raises(CouplingGuardError) as exc:
        get_mr_iid({})
    assert "CI_MERGE_REQUEST_IID" in str(exc.value)


def test_get_mr_iid_non_integer_raises() -> None:
    with pytest.raises(CouplingGuardError):
        get_mr_iid({"CI_MERGE_REQUEST_IID": "abc"})


def test_get_project_id_valid() -> None:
    assert get_project_id({"CI_PROJECT_ID": "123"}) == "123"


def test_get_project_id_missing_raises() -> None:
    with pytest.raises(CouplingGuardError):
        get_project_id({})


def test_find_existing_note_uses_all_pagination() -> None:
    mr = MagicMock()
    n1 = MagicMock()
    n1.body = "unrelated"
    n2 = MagicMock()
    n2.body = f"{MARKER}\nmine"
    mr.notes.list.return_value = [n1, n2]
    assert find_existing_note(mr) is n2
    mr.notes.list.assert_called_once_with(all=True)


def test_find_existing_note_no_match_returns_none() -> None:
    mr = MagicMock()
    mr.notes.list.return_value = [MagicMock(body="nope")]
    assert find_existing_note(mr) is None


def test_first_run_creates_note() -> None:
    mr = _mk_mr_no_existing()
    post_mr_note(mr, "the body", dry_run=False)
    mr.notes.create.assert_called_once_with({"body": "the body"})


def test_second_run_edits_via_save() -> None:
    existing = MagicMock()
    existing.body = MARKER
    mr = MagicMock()
    mr.notes.list.return_value = [existing]
    post_mr_note(mr, "updated body", dry_run=False)
    assert existing.body == "updated body"
    existing.save.assert_called_once()
    mr.notes.create.assert_not_called()


def test_dry_run_skips_api(capsys: pytest.CaptureFixture[str]) -> None:
    mr = MagicMock()
    post_mr_note(mr, "preview", dry_run=True)
    mr.notes.create.assert_not_called()
    mr.notes.list.assert_not_called()
    assert "preview" in capsys.readouterr().out


def test_run_gitlab_flow_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI_PROJECT_ID", "99")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")

    client = MagicMock()
    project = MagicMock()
    mr = _mk_mr_no_existing()
    client.projects.get.return_value = project
    project.mergerequests.get.return_value = mr

    rc = run_gitlab_flow(_mk_analysis(), "body", Config(), "tok", client=client)
    assert rc == 0
    mr.notes.create.assert_called_once_with({"body": "body"})


def test_run_gitlab_flow_fail_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI_PROJECT_ID", "99")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")

    client = MagicMock()
    project = MagicMock()
    mr = _mk_mr_no_existing()
    client.projects.get.return_value = project
    project.mergerequests.get.return_value = mr

    analysis = _mk_analysis(score=0.82, risk="high")
    rc = run_gitlab_flow(analysis, "body", Config(fail_threshold="high"), "tok", client=client)
    assert rc == 1


def test_run_gitlab_flow_auth_error_maps_to_couplingguard_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CI_PROJECT_ID", "99")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "7")

    client = MagicMock()
    client.projects.get.side_effect = gitlab.exceptions.GitlabAuthenticationError(
        response_code=401
    )

    with pytest.raises(CouplingGuardError) as exc:
        run_gitlab_flow(_mk_analysis(), "body", Config(), "tok", client=client)
    assert "authentication" in str(exc.value).lower()


def test_run_gitlab_flow_dry_run_skips_client(capsys: pytest.CaptureFixture[str]) -> None:
    rc = run_gitlab_flow(_mk_analysis(), "body", Config(dry_run=True), "tok", client=None)
    assert rc == 0
    assert "body" in capsys.readouterr().out
