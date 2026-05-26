from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import git
import pytest

from couplingguard.git_parser import (
    _decode_unicode_path,
    _is_binary,
    _normalize_rename,
    apply_excludes,
    get_commits,
    get_file_commit_counts,
    open_repo,
)
from couplingguard.models import CouplingGuardError, ShallowCloneError

# --- pure-function tests -------------------------------------------------


def test_normalize_rename_brace_same_dir() -> None:
    assert _normalize_rename("src/{old.py => new.py}") == "src/new.py"


def test_normalize_rename_brace_cross_dir() -> None:
    assert _normalize_rename("{old/dir => new/dir}/file.py") == "new/dir/file.py"


def test_normalize_rename_full_path_swap() -> None:
    assert _normalize_rename("old.py => new.py") == "new.py"


def test_normalize_rename_pass_through() -> None:
    assert _normalize_rename("src/foo.py") == "src/foo.py"


def test_decode_unicode_path_plain_pass_through() -> None:
    assert _decode_unicode_path("plain.py") == "plain.py"


def test_decode_unicode_path_octal_escapes() -> None:
    # git represents "café.py" as "caf\303\251.py" with literal backslashes.
    quoted = '"caf' + chr(92) + "303" + chr(92) + '251.py"'
    assert _decode_unicode_path(quoted) == "café.py"


def test_is_binary_common_extensions() -> None:
    assert _is_binary("logo.png")
    assert _is_binary("LOGO.PNG")
    assert _is_binary("dist/pkg.whl")
    assert _is_binary("lock.lock")
    assert not _is_binary("a.py")
    assert not _is_binary("README.md")


def test_apply_excludes_glob() -> None:
    assert apply_excludes(["a.py", "docs/b.md"], ["docs/**"]) == ["a.py"]
    assert apply_excludes(["a.py"], []) == ["a.py"]
    assert apply_excludes(["a.py", "b.py"], ["*.py"]) == []


# --- real-repo tests -----------------------------------------------------


def test_open_repo_invalid_path(tmp_path: Path) -> None:
    with pytest.raises(CouplingGuardError):
        open_repo(tmp_path)


def test_open_repo_nonexistent_path() -> None:
    with pytest.raises(CouplingGuardError):
        open_repo(Path("/this/path/does/not/exist/anywhere"))


def test_shallow_clone_raises(
    fake_repo: git.Repo,
    commit_files: Callable[..., git.Commit],
    tmp_path: Path,
) -> None:
    # Create a few commits, then make a shallow clone and verify open_repo raises.
    # `--no-local` forces git to use the wire protocol against the file:// URL
    # so `--depth=1` actually takes effect (a plain local clone hard-links by
    # default and ignores depth).
    commit_files(["a.py", "b.py"], "init")
    commit_files(["a.py"], "second")
    commit_files(["a.py"], "third")

    shallow_path = tmp_path.parent / (tmp_path.name + "-shallow")
    git.Repo.clone_from(
        f"file://{tmp_path.as_posix()}",
        str(shallow_path),
        depth=1,
        no_local=True,
    )
    shallow_repo = git.Repo(shallow_path)
    try:
        # Sanity check: confirm the shallow file actually exists.
        assert (shallow_path / ".git" / "shallow").exists()
        with pytest.raises(ShallowCloneError) as exc:
            open_repo(shallow_path)
        assert "fetch-depth: 0" in str(exc.value)
    finally:
        shallow_repo.close()


def test_lookback_includes_recent_commit(
    fake_repo: git.Repo, commit_files: Callable[..., git.Commit]
) -> None:
    commit_files(["a.py"], "c1")
    commits = get_commits(fake_repo, lookback_days=30)
    assert len(commits) >= 1
    assert "a.py" in commits[0]


def test_merge_commits_excluded(
    fake_repo: git.Repo, commit_files: Callable[..., git.Commit]
) -> None:
    commit_files(["a.py"], "init")
    commit_files(["b.py"], "second")
    fake_repo.git.checkout("-b", "feat")
    commit_files(["c.py"], "on feat")
    fake_repo.git.checkout("main")
    fake_repo.git.merge("feat", "--no-ff", "-m", "merge")

    commits = get_commits(fake_repo, lookback_days=30)
    # We have 4 actual commits (init, second, on-feat, merge) but merge is excluded.
    assert len(commits) == 3


def test_binary_files_filtered(
    fake_repo: git.Repo, commit_files: Callable[..., git.Commit], tmp_path: Path
) -> None:
    (tmp_path / "logo.png").write_bytes(b"PNG")
    fake_repo.index.add(["logo.png"])
    commit_files(["a.py"], "init")
    # The above commit_files call added a.py and committed; logo.png is unstaged.
    # Re-stage and commit again together:
    (tmp_path / "logo.png").write_bytes(b"PNG-new")
    (tmp_path / "a.py").write_text("after")
    fake_repo.index.add(["a.py", "logo.png"])
    fake_repo.index.commit("with binary")

    commits = get_commits(fake_repo, lookback_days=30)
    for c in commits:
        assert "logo.png" not in c


def test_exclude_pattern_applied_during_walk(
    fake_repo: git.Repo, commit_files: Callable[..., git.Commit]
) -> None:
    commit_files(["src/app.py", "docs/readme.md"], "init")
    commits = get_commits(fake_repo, lookback_days=30, exclude_patterns=["docs/**"])
    for c in commits:
        assert all(not f.startswith("docs/") for f in c)


def test_file_commit_counts() -> None:
    commits = [["a", "b"], ["a"], ["a", "c"]]
    counts = get_file_commit_counts(commits)
    assert counts == {"a": 3, "b": 1, "c": 1}


def test_empty_history_returns_empty(
    fake_repo: git.Repo,
) -> None:
    commits = get_commits(fake_repo, lookback_days=30)
    assert commits == []
