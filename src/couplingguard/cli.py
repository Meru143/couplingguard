from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from . import run
from .config import parse_action_inputs


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="couplingguard",
        description=(
            "Detect file coupling risk in pull requests from git co-change history. "
            "Designed to run inside a GitHub Actions or GitLab CI job, but can be "
            "invoked locally with --dry-run for a preview."
        ),
    )
    p.add_argument(
        "--repo",
        default=".",
        help="Path to the git repository root (default: current directory).",
    )
    p.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Days of git history to analyze (default: 90).",
    )
    p.add_argument(
        "--min-occurrences",
        type=int,
        default=None,
        help="Minimum co-change count to include a pair (default: 3).",
    )
    p.add_argument(
        "--max-pairs",
        type=int,
        default=None,
        help="Maximum pairs to show in the comment (default: 10).",
    )
    p.add_argument(
        "--low-threshold",
        type=float,
        default=None,
        help="Score boundary for low risk (default: 0.3).",
    )
    p.add_argument(
        "--high-threshold",
        type=float,
        default=None,
        help="Score boundary for high risk (default: 0.7).",
    )
    p.add_argument(
        "--fail-threshold",
        choices=["low", "medium", "high"],
        default=None,
        help="Exit 1 if any pair crosses this level. Omit for never-fail mode.",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="GLOB",
        help="Path pattern to exclude (repeatable).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the comment body to stdout instead of posting it.",
    )
    p.add_argument(
        "--publish-dashboard",
        action="store_true",
        help="Write coupling-history.json, coupling-dashboard.html, and coupling-score.json.",
    )
    return p


def _args_to_inputs(args: argparse.Namespace) -> dict[str, Any]:
    """Convert argparse Namespace to the same dict shape as parse_action_inputs."""
    inputs: dict[str, Any] = {}
    if args.lookback_days is not None:
        inputs["lookback_days"] = args.lookback_days
    if args.min_occurrences is not None:
        inputs["min_occurrences"] = args.min_occurrences
    if args.max_pairs is not None:
        inputs["max_pairs"] = args.max_pairs
    if args.low_threshold is not None:
        inputs["low_threshold"] = args.low_threshold
    if args.high_threshold is not None:
        inputs["high_threshold"] = args.high_threshold
    if args.fail_threshold is not None:
        inputs["fail_threshold"] = args.fail_threshold
    if args.exclude:
        inputs["exclude"] = list(args.exclude)
    if args.dry_run:
        inputs["dry_run"] = True
    if args.publish_dashboard:
        inputs["publish_dashboard"] = True
    return inputs


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # When invoked under GitHub Actions, INPUT_* env vars drive config.
    # When invoked from the local CLI, argparse drives it. Locally we
    # merge env-derived inputs (lower priority) under CLI flags so users
    # who set INPUT_* manually can still override on the command line.
    env_inputs = parse_action_inputs() if any(
        k.startswith("INPUT_") for k in os.environ
    ) else {}
    cli_inputs = _args_to_inputs(args)
    inputs: dict[str, Any] = {**env_inputs, **cli_inputs}

    return run(Path(args.repo).resolve(), inputs)


def _entrypoint() -> None:
    sys.exit(main())


if __name__ == "__main__":
    _entrypoint()
