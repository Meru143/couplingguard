"""Dogfood test: run couplingguard against its own repository.

This catches regressions that unit tests can't see — e.g. the algorithm
producing nonsense scores on real-world git history, or a refactor
breaking the end-to-end pipeline against a repo with many real commits
of various shapes (merge commits, renames, binary files, etc.).
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import git
import pytest

from couplingguard import run

REPO_ROOT = Path(__file__).resolve().parents[2]


def _is_couplingguard_repo() -> bool:
    """Skip if we're not running from inside couplingguard's own repo
    (e.g. when this file was extracted into a wheel for cross-repo
    testing).
    """
    return (REPO_ROOT / "src" / "couplingguard" / "__init__.py").is_file()


@pytest.mark.skipif(
    not _is_couplingguard_repo(),
    reason="dogfood test requires running from couplingguard's own checkout",
)
def test_run_against_own_repo_does_not_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pick a small window of couplingguard's own history, build a fake
    PR event around it, and confirm run() completes with exit 0 and
    emits a marker-tagged comment to stdout.
    """
    repo = git.Repo(REPO_ROOT)
    try:
        commits = list(repo.iter_commits("HEAD", max_count=10))
        assert len(commits) >= 2, "expected at least 2 commits in our own repo"
        head_sha = commits[0].hexsha
        # Use a commit 4-5 back so the synthetic PR diff includes a
        # meaningful number of files instead of a single docs-only commit.
        base_sha = commits[min(5, len(commits) - 1)].hexsha

        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "pull_request": {
                        "number": 9999,
                        "base": {"sha": base_sha},
                        "head": {"sha": head_sha},
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

        # Capture stdout because dry_run prints the comment body there.
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run(
                REPO_ROOT,
                {
                    "dry_run": True,
                    "min_occurrences": 2,
                    "lookback_days": 365,
                    "max_pairs": 8,
                },
            )
        output = buf.getvalue()

        assert rc == 0, f"run() failed against own repo: {output[-500:]}"
        assert "<!-- couplingguard:marker -->" in output, (
            "expected the hidden marker in dry-run output, got:\n" + output[:1000]
        )
        # Either we found coupling pairs, or we got the informational
        # "no coupling detected" message — both are valid healthy outputs.
        assert "couplingguard:data:" in output
    finally:
        repo.close()


@pytest.mark.skipif(
    not _is_couplingguard_repo(),
    reason="dogfood test requires running from couplingguard's own checkout",
)
def test_dogfood_output_shape_matches_renderer_spec(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dry-run output must always parse back through the delta extractor.

    This guards against renderer changes that accidentally invalidate
    the hidden JSON blob — without this we wouldn't notice until a real
    PR re-push tried to compute a delta.
    """
    from couplingguard.delta import extract_previous_data

    repo = git.Repo(REPO_ROOT)
    try:
        commits = list(repo.iter_commits("HEAD", max_count=10))
        head_sha = commits[0].hexsha
        base_sha = commits[min(5, len(commits) - 1)].hexsha

        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "pull_request": {
                        "number": 9999,
                        "base": {"sha": base_sha},
                        "head": {"sha": head_sha},
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

        buf = io.StringIO()
        with redirect_stdout(buf):
            run(REPO_ROOT, {"dry_run": True, "min_occurrences": 2, "lookback_days": 365})
        output = buf.getvalue()

        data = extract_previous_data(output)
        assert data is not None, "dogfood output's data marker did not parse"
        assert "max_score" in data
        assert isinstance(data["max_score"], (int, float))
        assert 0.0 <= float(data["max_score"]) <= 1.0
    finally:
        repo.close()
