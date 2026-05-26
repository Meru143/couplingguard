"""Tests for the argparse CLI wrapper around run()."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from couplingguard.cli import _args_to_inputs, _build_parser, main


def test_parser_basic_defaults() -> None:
    parser = _build_parser()
    args = parser.parse_args([])
    assert args.repo == "."
    assert args.lookback_days is None
    assert args.min_occurrences is None
    assert args.dry_run is False
    assert args.publish_dashboard is False


def test_parser_all_options() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        [
            "--repo", "/tmp/x",
            "--lookback-days", "180",
            "--min-occurrences", "5",
            "--max-pairs", "20",
            "--low-threshold", "0.2",
            "--high-threshold", "0.8",
            "--fail-threshold", "high",
            "--exclude", "docs/**",
            "--exclude", "*.md",
            "--dry-run",
            "--publish-dashboard",
        ]
    )
    assert args.repo == "/tmp/x"
    assert args.lookback_days == 180
    assert args.min_occurrences == 5
    assert args.fail_threshold == "high"
    assert args.exclude == ["docs/**", "*.md"]
    assert args.dry_run is True


def test_parser_rejects_invalid_fail_threshold() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--fail-threshold", "extreme"])


def test_args_to_inputs_includes_only_explicit_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args([])
    assert _args_to_inputs(args) == {}


def test_args_to_inputs_with_values() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        ["--lookback-days", "30", "--dry-run", "--exclude", "x"]
    )
    inputs = _args_to_inputs(args)
    assert inputs["lookback_days"] == 30
    assert inputs["dry_run"] is True
    assert inputs["exclude"] == ["x"]
    assert "min_occurrences" not in inputs


def test_main_calls_run_with_correct_arguments(tmp_path: Path) -> None:
    """main() should resolve the repo path and pass our inputs to run()."""
    with patch("couplingguard.cli.run", return_value=0) as mock_run:
        rc = main(["--repo", str(tmp_path), "--dry-run", "--lookback-days", "30"])
    assert rc == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    # First positional: resolved repo path
    assert call_args[0][0] == tmp_path.resolve()
    # Second positional: inputs dict
    inputs = call_args[0][1]
    assert inputs["dry_run"] is True
    assert inputs["lookback_days"] == 30


def test_main_returns_run_exit_code(tmp_path: Path) -> None:
    with patch("couplingguard.cli.run", return_value=1):
        rc = main(["--repo", str(tmp_path), "--dry-run"])
    assert rc == 1


def test_main_merges_env_inputs_under_cli_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If both INPUT_* env vars and CLI flags set the same field, CLI wins."""
    monkeypatch.setenv("INPUT_LOOKBACK_DAYS", "180")
    monkeypatch.setenv("INPUT_MIN_OCCURRENCES", "5")
    with patch("couplingguard.cli.run", return_value=0) as mock_run:
        main(["--repo", str(tmp_path), "--lookback-days", "30"])
    inputs = mock_run.call_args[0][1]
    assert inputs["lookback_days"] == 30  # CLI wins
    assert inputs["min_occurrences"] == 5  # env-only, kept


def test_main_uses_env_inputs_when_no_cli_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INPUT_LOOKBACK_DAYS", "180")
    with patch("couplingguard.cli.run", return_value=0) as mock_run:
        main(["--repo", str(tmp_path)])
    inputs = mock_run.call_args[0][1]
    assert inputs["lookback_days"] == 180
