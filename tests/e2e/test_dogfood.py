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
from couplingguard.delta import extract_previous_data

REPO_ROOT = Path(__file__).resolve().parents[2]


def _is_couplingguard_repo() -> bool:
    """Skip if we're not running from inside couplingguard's own repo
    (e.g. when this file was extracted into a wheel for cross-repo
    testing).
    """
    return (REPO_ROOT / "src" / "couplingguard" / "__init__.py").is_file()


def _run_dogfood(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[int, str, list[str]]:
    """Build a wide synthetic PR (10 commits back ... HEAD) and run couplingguard
    against it. Returns (exit_code, captured_stdout, diff_file_list).
    """
    repo = git.Repo(REPO_ROOT)
    try:
        commits = list(repo.iter_commits("HEAD", max_count=12))
        assert len(commits) >= 2, "expected at least 2 commits in our own repo"
        head_sha = commits[0].hexsha
        # Wide window: 10 commits back so the diff includes both src/ and
        # config files, giving the algorithm enough surface to find pairs.
        base_sha = commits[min(10, len(commits) - 1)].hexsha
        diff_files = [
            f for f in repo.git.diff("--name-only", f"{base_sha}...{head_sha}").splitlines()
            if f.strip()
        ]

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
            rc = run(
                REPO_ROOT,
                {
                    "dry_run": True,
                    "min_occurrences": 2,
                    "lookback_days": 365,
                    "max_pairs": 8,
                },
            )
        return rc, buf.getvalue(), diff_files
    finally:
        repo.close()


@pytest.mark.skipif(
    not _is_couplingguard_repo(),
    reason="dogfood test requires running from couplingguard's own checkout",
)
def test_dogfood_run_against_own_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The full pipeline must complete with exit 0 and emit the marker."""
    rc, output, _ = _run_dogfood(tmp_path, monkeypatch)
    assert rc == 0, f"run() exited {rc}; last 500 chars:\n{output[-500:]}"
    assert "<!-- couplingguard:marker -->" in output


@pytest.mark.skipif(
    not _is_couplingguard_repo(),
    reason="dogfood test requires running from couplingguard's own checkout",
)
def test_dogfood_data_blob_round_trips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hidden JSON marker must parse back through the delta extractor."""
    _, output, _ = _run_dogfood(tmp_path, monkeypatch)
    data = extract_previous_data(output)
    assert data is not None, "dogfood output's data marker did not parse"
    assert "max_score" in data
    score = float(data["max_score"])
    assert 0.0 <= score <= 1.0, f"max_score {score} outside [0, 1]"


@pytest.mark.skipif(
    not _is_couplingguard_repo(),
    reason="dogfood test requires running from couplingguard's own checkout",
)
def test_dogfood_finds_at_least_one_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 10-commit-wide synthetic PR against couplingguard's own history
    must surface at least one coupling pair.

    couplingguard's history has many commits that touch paired source
    and test files (e.g. matrix.py + test_matrix.py landed together).
    If this test ever returns zero pairs it means either the matrix
    builder regressed or the PR analyzer's filter logic is broken —
    both are real algorithm bugs unit tests would miss.
    """
    _, output, diff_files = _run_dogfood(tmp_path, monkeypatch)
    data = extract_previous_data(output)
    assert data is not None

    if "No coupling patterns detected" in output:
        pytest.fail(
            "Algorithm found zero coupling pairs on a 10-commit-wide synthetic PR. "
            f"This usually means the matrix builder or PR analyzer regressed. "
            f"Diff included {len(diff_files)} files: {diff_files[:5]}..."
        )

    # The `scores` dict in the data blob maps each PR file to its
    # max-pair score. A healthy dogfood run on this repo has at least
    # one PR file with a positive score.
    scores = data.get("scores", {})
    assert isinstance(scores, dict)
    assert len(scores) >= 1, f"expected >=1 file with coupling, got {scores}"
    assert any(float(s) > 0.0 for s in scores.values()), (
        f"expected at least one positive coupling score, got {scores}"
    )


@pytest.mark.skipif(
    not _is_couplingguard_repo(),
    reason="dogfood test requires running from couplingguard's own checkout",
)
def test_dogfood_score_distribution_looks_sensible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity-check the score distribution against the rendered table.

    Each row in the markdown table must be:
      * a recognized risk emoji (🟢 / 🟡 / 🔴)
      * a 0.00-1.00 score
      * co_changes <= total_commits (you can't co-change more often
        than the more-frequently-changed file changed at all)
    """
    _, output, _ = _run_dogfood(tmp_path, monkeypatch)
    if "No coupling patterns detected" in output:
        pytest.skip("zero pairs found — covered by test_dogfood_finds_at_least_one_pair")

    table_rows = [
        line for line in output.splitlines()
        if line.startswith("| `") and "commits |" in line
    ]
    assert len(table_rows) >= 1, "expected at least one table row in output"

    for row in table_rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        # Cells: [file_in_pr, coupled, score, risk, co/total commits]
        assert len(cells) == 5, f"unexpected table row shape: {row!r}"
        score = float(cells[2])
        assert 0.0 <= score <= 1.0, f"score {score} outside [0, 1] in: {row!r}"
        assert any(emoji in cells[3] for emoji in ("🟢", "🟡", "🔴")), (
            f"missing risk emoji in: {row!r}"
        )
        co, total = cells[4].replace(" commits", "").split("/")
        assert int(co) <= int(total), (
            f"co_changes ({co}) > total_commits ({total}) in: {row!r}"
        )
