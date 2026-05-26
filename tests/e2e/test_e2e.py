"""End-to-end pipeline tests: real git repo + fake event payload + run()."""

from __future__ import annotations

import json
from pathlib import Path

import git
import pytest

from couplingguard import run


@pytest.fixture
def e2e_repo(tmp_path: Path) -> git.Repo:
    repo = git.Repo.init(tmp_path, initial_branch="main")
    with repo.config_writer() as cw:
        cw.set_value("user", "email", "e2e@example.com")
        cw.set_value("user", "name", "E2E")
    return repo


def _commit(repo: git.Repo, root: Path, files: list[str], message: str) -> git.Commit:
    for f in files:
        p = root / f
        p.parent.mkdir(parents=True, exist_ok=True)
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
        p.write_text(existing + f"\n{message}", encoding="utf-8")
    repo.index.add(files)
    return repo.index.commit(message)


def _write_event(
    root: Path, pr_number: int, base_sha: str, head_sha: str, monkeypatch: pytest.MonkeyPatch
) -> Path:
    payload = {
        "pull_request": {
            "number": pr_number,
            "base": {"sha": base_sha},
            "head": {"sha": head_sha},
        }
    }
    path = root / "event.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    return path


def test_coupling_detected_in_real_repo(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """8 of 9 commits to a.py also touch b.py -> score 8/9 ≈ 0.89 (🔴 high)."""
    # 8 paired commits + 1 solo commit on a.py to vary the totals.
    for i in range(8):
        _commit(e2e_repo, tmp_path, ["a.py", "b.py"], f"pair {i}")
    _commit(e2e_repo, tmp_path, ["a.py"], "solo")

    base = e2e_repo.head.commit.hexsha
    head_commit = _commit(e2e_repo, tmp_path, ["a.py"], "PR change")
    head = head_commit.hexsha

    _write_event(tmp_path, 42, base, head, monkeypatch)

    rc = run(tmp_path, {"dry_run": True, "min_occurrences": 3, "lookback_days": 90})
    assert rc == 0

    out = capsys.readouterr().out
    assert "couplingguard:marker" in out
    assert "a.py" in out and "b.py" in out
    # Expected score: 8 co-changes / max(a=10 commits, b=8 commits) = 8/10 = 0.80
    # (a.py appears in 8 paired commits + 1 solo + 1 PR change = 10)
    assert "0.80" in out
    assert "8/10 commits" in out
    assert "🔴" in out  # 0.80 > high_threshold 0.7
    e2e_repo.close()


def test_pr_with_no_changed_files_posts_info_and_exits_zero(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When base == head, git diff returns nothing -> info comment + exit 0."""
    for _ in range(5):
        _commit(e2e_repo, tmp_path, ["a.py", "b.py"], "init+")

    sha = e2e_repo.head.commit.hexsha
    _write_event(tmp_path, 1, sha, sha, monkeypatch)

    rc = run(tmp_path, {"dry_run": True, "min_occurrences": 3})
    assert rc == 0
    out = capsys.readouterr().out
    assert "No changed files detected" in out
    e2e_repo.close()


def test_too_few_commits_posts_info_and_exits_zero(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """min_occurrences=5 but only 2 commits -> info comment, exit 0."""
    _commit(e2e_repo, tmp_path, ["a.py", "b.py"], "c1")
    base = e2e_repo.head.commit.hexsha
    head_commit = _commit(e2e_repo, tmp_path, ["a.py"], "c2")
    head = head_commit.hexsha

    _write_event(tmp_path, 1, base, head, monkeypatch)

    rc = run(tmp_path, {"dry_run": True, "min_occurrences": 5})
    assert rc == 0
    out = capsys.readouterr().out
    assert "not enough git history" in out
    e2e_repo.close()


def test_fail_threshold_triggers_exit_code_one(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Strong coupling + fail_threshold=high -> exit 1."""
    for i in range(8):
        _commit(e2e_repo, tmp_path, ["a.py", "b.py"], f"pair {i}")

    base = e2e_repo.head.commit.hexsha
    head_commit = _commit(e2e_repo, tmp_path, ["a.py"], "PR")
    head = head_commit.hexsha

    _write_event(tmp_path, 99, base, head, monkeypatch)

    rc = run(
        tmp_path,
        {"dry_run": True, "min_occurrences": 3, "fail_threshold": "high"},
    )
    assert rc == 1
    e2e_repo.close()


def test_exclude_pattern_removes_files_from_analysis(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """docs/** glob removes those files; remaining pairs should not include them."""
    for i in range(5):
        _commit(e2e_repo, tmp_path, ["src/a.py", "docs/x.md"], f"with docs {i}")

    base = e2e_repo.head.commit.hexsha
    head_commit = _commit(e2e_repo, tmp_path, ["src/a.py"], "PR")
    head = head_commit.hexsha

    _write_event(tmp_path, 1, base, head, monkeypatch)

    rc = run(
        tmp_path,
        {
            "dry_run": True,
            "min_occurrences": 3,
            "exclude": ["docs/**"],
        },
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "docs/x.md" not in out
    e2e_repo.close()


def test_publish_dashboard_writes_artifact_files(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for i in range(5):
        _commit(e2e_repo, tmp_path, ["a.py", "b.py"], f"pair {i}")

    base = e2e_repo.head.commit.hexsha
    head_commit = _commit(e2e_repo, tmp_path, ["a.py"], "PR")
    head = head_commit.hexsha

    _write_event(tmp_path, 1, base, head, monkeypatch)

    rc = run(
        tmp_path,
        {"dry_run": True, "min_occurrences": 3, "publish_dashboard": True},
    )
    assert rc == 0
    assert (tmp_path / "coupling-history.json").exists()
    assert (tmp_path / "coupling-dashboard.html").exists()
    assert (tmp_path / "coupling-score.json").exists()
    # Quick shape sanity check
    history = json.loads((tmp_path / "coupling-history.json").read_text(encoding="utf-8"))
    assert len(history) == 1
    assert history[0]["pr"] == 1
    e2e_repo.close()


def test_shallow_clone_returns_exit_one(
    e2e_repo: git.Repo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Shallow clone -> ShallowCloneError -> info comment + exit 1."""
    _commit(e2e_repo, tmp_path, ["a.py"], "init")
    _commit(e2e_repo, tmp_path, ["a.py"], "second")

    shallow_path = tmp_path.parent / (tmp_path.name + "-e2e-shallow")
    git.Repo.clone_from(
        f"file://{tmp_path.as_posix()}",
        str(shallow_path),
        depth=1,
        no_local=True,
    )
    shallow = git.Repo(shallow_path)

    # Fake event with the shallow's HEAD as both base and head (irrelevant —
    # we expect to fail before we read the event).
    head = shallow.head.commit.hexsha
    _write_event(shallow_path, 1, head, head, monkeypatch)

    try:
        rc = run(shallow_path, {"dry_run": True})
        assert rc == 1
        out = capsys.readouterr().out
        assert "shallow clone" in out.lower()
    finally:
        shallow.close()
        e2e_repo.close()
