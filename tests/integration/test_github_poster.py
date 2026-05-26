from __future__ import annotations

from unittest.mock import MagicMock, patch

import github
import pytest

from couplingguard.github_poster import (
    MARKER,
    check_fail_threshold,
    find_existing_comment,
    get_github_client,
    post_comment,
    run_github_flow,
)
from couplingguard.models import (
    Config,
    CouplingGuardError,
    CouplingPair,
    GitHubAuthError,
    PRAnalysis,
)


def _mk_pr_with_no_existing_comment() -> MagicMock:
    pr = MagicMock()
    pr.get_issue_comments.return_value = []
    return pr


def _mk_pr_with_existing_comment() -> tuple[MagicMock, MagicMock]:
    existing = MagicMock()
    existing.body = f"{MARKER}\nold body"
    pr = MagicMock()
    pr.get_issue_comments.return_value = [existing]
    return pr, existing


def _mk_analysis(score: float = 0.5, risk: str = "medium") -> PRAnalysis:
    return PRAnalysis(
        pr_number=42,
        pr_files=["a.py"],
        pairs=[CouplingPair("a.py", "b.py", score, 5, 10, risk)],
        max_score=score,
        pr_risk=risk,
    )


def test_first_run_creates_comment() -> None:
    pr = _mk_pr_with_no_existing_comment()
    post_comment(pr, "the body", dry_run=False)
    pr.create_issue_comment.assert_called_once_with("the body")


def test_second_run_edits_existing_comment() -> None:
    pr, existing = _mk_pr_with_existing_comment()
    post_comment(pr, "new body", dry_run=False)
    existing.edit.assert_called_once_with("new body")
    pr.create_issue_comment.assert_not_called()


def test_dry_run_does_not_call_api(capsys: pytest.CaptureFixture[str]) -> None:
    pr = MagicMock()
    post_comment(pr, "dry body", dry_run=True)
    pr.get_issue_comments.assert_not_called()
    pr.create_issue_comment.assert_not_called()
    captured = capsys.readouterr()
    assert "dry body" in captured.out


def test_find_existing_skips_non_marker_comments() -> None:
    pr = MagicMock()
    c1 = MagicMock(); c1.body = "random unrelated comment"
    c2 = MagicMock(); c2.body = f"{MARKER}\nmine"
    pr.get_issue_comments.return_value = [c1, c2]
    found = find_existing_comment(pr)
    assert found is c2


def test_github_exception_403_maps_to_auth_error() -> None:
    pr = _mk_pr_with_no_existing_comment()
    pr.create_issue_comment.side_effect = github.GithubException(
        403, data={"message": "forbidden"}, headers={}
    )
    with pytest.raises(GitHubAuthError) as exc:
        post_comment(pr, "body", dry_run=False)
    assert "pull-requests: write" in str(exc.value)


def test_github_exception_other_status_maps_to_couplingguard_error() -> None:
    pr = _mk_pr_with_no_existing_comment()
    pr.create_issue_comment.side_effect = github.GithubException(
        422, data={"message": "validation failed"}, headers={}
    )
    with pytest.raises(CouplingGuardError) as exc:
        post_comment(pr, "body", dry_run=False)
    assert "status=422" in str(exc.value)


def test_rate_limit_triggers_sleep_then_retries() -> None:
    pr = _mk_pr_with_no_existing_comment()
    rate_limit_exc = github.RateLimitExceededException(
        403, data={}, headers={"x-ratelimit-reset": "1"}
    )
    pr.create_issue_comment.side_effect = [rate_limit_exc, None]
    with patch("couplingguard.github_poster.time.sleep") as mock_sleep:
        post_comment(pr, "body", dry_run=False)
        mock_sleep.assert_called_once()
    assert pr.create_issue_comment.call_count == 2


def test_persistent_rate_limit_re_raises_after_retry() -> None:
    pr = _mk_pr_with_no_existing_comment()
    rate_limit_exc = github.RateLimitExceededException(
        403, data={}, headers={"x-ratelimit-reset": "1"}
    )
    pr.create_issue_comment.side_effect = [rate_limit_exc, rate_limit_exc]
    with patch("couplingguard.github_poster.time.sleep"):
        with pytest.raises(github.RateLimitExceededException):
            post_comment(pr, "body", dry_run=False)


def test_check_fail_threshold_none_returns_false() -> None:
    analysis = _mk_analysis(score=0.99, risk="high")
    assert check_fail_threshold(analysis, Config(fail_threshold=None)) is False


def test_check_fail_threshold_high_with_high_score() -> None:
    analysis = _mk_analysis(score=0.82, risk="high")
    assert check_fail_threshold(analysis, Config(fail_threshold="high")) is True


def test_check_fail_threshold_high_with_medium_score() -> None:
    analysis = _mk_analysis(score=0.6, risk="medium")
    assert check_fail_threshold(analysis, Config(fail_threshold="high")) is False


def test_check_fail_threshold_low_fails_on_any_pair() -> None:
    analysis = _mk_analysis(score=0.01, risk="low")
    assert check_fail_threshold(analysis, Config(fail_threshold="low")) is True


def test_check_fail_threshold_invalid_value_raises() -> None:
    analysis = _mk_analysis()
    with pytest.raises(CouplingGuardError):
        check_fail_threshold(analysis, Config(fail_threshold="extreme"))


def test_check_fail_threshold_no_pairs_never_fails() -> None:
    analysis = PRAnalysis(1, ["a"], [], 0.0, "low")
    assert check_fail_threshold(analysis, Config(fail_threshold="low")) is False


def test_run_github_flow_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "Meru143/couplingguard")
    client = MagicMock()
    repo = MagicMock()
    pr = _mk_pr_with_no_existing_comment()
    client.get_repo.return_value = repo
    repo.get_pull.return_value = pr

    analysis = _mk_analysis(score=0.4)
    rc = run_github_flow(analysis, "body", Config(), token="t", client=client)
    assert rc == 0
    pr.create_issue_comment.assert_called_once_with("body")


def test_run_github_flow_fails_with_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "Meru143/couplingguard")
    client = MagicMock()
    repo = MagicMock()
    pr = _mk_pr_with_no_existing_comment()
    client.get_repo.return_value = repo
    repo.get_pull.return_value = pr

    analysis = _mk_analysis(score=0.82, risk="high")
    rc = run_github_flow(analysis, "body", Config(fail_threshold="high"), token="t", client=client)
    assert rc == 1


def test_run_github_flow_dry_run_skips_client(capsys: pytest.CaptureFixture[str]) -> None:
    analysis = _mk_analysis()
    rc = run_github_flow(analysis, "body", Config(dry_run=True), token="t", client=None)
    assert rc == 0
    out = capsys.readouterr().out
    assert "body" in out


def test_run_github_flow_missing_repo_env_raises() -> None:
    client = MagicMock()
    analysis = _mk_analysis()
    with pytest.raises(CouplingGuardError) as exc:
        run_github_flow(analysis, "body", Config(), token="t", client=client)
    assert "GITHUB_REPOSITORY" in str(exc.value)


def test_get_github_client_empty_token_raises() -> None:
    with pytest.raises(GitHubAuthError):
        get_github_client("")
