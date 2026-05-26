from __future__ import annotations

from pathlib import Path

from codeowners import CodeOwners

from couplingguard.codeowners_loader import (
    get_owners,
    load_codeowners,
    suggest_reviewers,
)
from couplingguard.models import CouplingPair


def test_load_codeowners_missing_returns_none(tmp_path: Path) -> None:
    assert load_codeowners(tmp_path) is None


def test_load_codeowners_found_in_github_dir(tmp_path: Path) -> None:
    gh = tmp_path / ".github"
    gh.mkdir()
    (gh / "CODEOWNERS").write_text("* @alice\n")
    co = load_codeowners(tmp_path)
    assert co is not None


def test_load_codeowners_found_at_root(tmp_path: Path) -> None:
    (tmp_path / "CODEOWNERS").write_text("*.py @bob\n")
    co = load_codeowners(tmp_path)
    assert co is not None


def test_load_codeowners_found_in_docs(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "CODEOWNERS").write_text("*.md @docs-team\n")
    co = load_codeowners(tmp_path)
    assert co is not None


def test_get_owners_username_type() -> None:
    co = CodeOwners("*.py @alice\n")
    assert get_owners(co, "foo.py") == ["@alice"]


def test_get_owners_email_type() -> None:
    co = CodeOwners("*.py bob@example.com\n")
    owners = get_owners(co, "foo.py")
    assert "bob@example.com" in owners


def test_get_owners_mixed_username_and_email() -> None:
    co = CodeOwners("*.py @alice bob@example.com\n")
    owners = get_owners(co, "foo.py")
    assert "@alice" in owners and "bob@example.com" in owners


def test_get_owners_no_match() -> None:
    co = CodeOwners("*.py @alice\n")
    assert get_owners(co, "README.md") == []


def test_suggest_reviewers_none_codeowners_returns_empty() -> None:
    pair = CouplingPair("a.py", "b.py", 0.5, 5, 10, "medium")
    assert suggest_reviewers([pair], None, ["a.py"]) == []
    assert pair.suggested_owners == []


def test_suggest_reviewers_excludes_pr_file_owners() -> None:
    co = CodeOwners(
        "a.py @alice\n"
        "b.py @bob @alice\n"
        "c.py @carol\n"
    )
    p1 = CouplingPair("a.py", "b.py", 0.8, 10, 12, "high")
    p2 = CouplingPair("a.py", "c.py", 0.5, 6, 12, "medium")
    suggested = suggest_reviewers([p1, p2], co, ["a.py"])
    # @alice owns a.py (in the PR), so they're filtered out everywhere.
    assert p1.suggested_owners == ["@bob"]
    assert p2.suggested_owners == ["@carol"]
    assert suggested == ["@bob", "@carol"]


def test_suggest_reviewers_dedup_preserves_order() -> None:
    co = CodeOwners(
        "b.py @x @y\n"
        "c.py @y @z\n"
    )
    p1 = CouplingPair("a.py", "b.py", 0.8, 10, 12, "high")
    p2 = CouplingPair("a.py", "c.py", 0.5, 6, 12, "medium")
    # @y appears in both pairs; the aggregated list should keep first-seen order
    suggested = suggest_reviewers([p1, p2], co, [])
    assert suggested == ["@x", "@y", "@z"]


def test_suggest_reviewers_no_pairs_returns_empty() -> None:
    co = CodeOwners("* @alice\n")
    assert suggest_reviewers([], co, []) == []
