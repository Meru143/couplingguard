# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] — 2026-05-27

### Changed
- **Algorithm extracted to [`coupling-core`](https://pypi.org/project/coupling-core/) (>=1.0.1, <2.0).**
  The git-history parser and co-change matrix builder no longer ship in this
  package — they live in `coupling-core`, a standalone library that any
  project can consume for co-change analysis. couplingguard now depends on
  it and consumes its public API. No user-facing behaviour change: install
  resolves both packages, the Action runs identically, and the PR comment
  output is byte-for-byte the same.
- `couplingguard.models.CouplingGuardError` is now an alias for
  `coupling_core.CouplingCoreError` (same class object, two names), and
  `couplingguard.models.ShallowCloneError` is an alias for
  `coupling_core.ShallowCloneError`. Code that catches either name keeps
  working; new code can use either interchangeably. `ConfigError` and
  `GitHubAuthError` remain couplingguard-specific subclasses.

### Removed
- `couplingguard.git_parser` module (moved to `coupling_core.git_parser`).
- `couplingguard.matrix` module (moved to `coupling_core.matrix`).
- 28 unit tests that exercised the extracted modules (now upstream in
  coupling-core's own test suite). The end-to-end and dogfood tests still
  exercise the full pipeline through coupling-core.

### Internal
- Test count: 148 (was 177; the 29-test drop reflects only the extracted
  unit tests).
- coverage, ruff, mypy `--strict` all still clean.

## [0.1.1] — 2026-05-26

### Fixed
- Release workflow now syncs the `pyproject.toml` and
  `src/couplingguard/__init__.py` version to the tag-derived PEP 440
  version *before* `python -m build` runs. The previous workflow only
  verified the base version matched and let the build read the static
  `pyproject.toml` version, so a pre-release tag like `v0.1.0-rc1`
  produced a `0.1.0` (not `0.1.0rc1`) wheel.
- `v0.1.0` on PyPI is yanked. Use `0.1.1` going forward.

## [0.1.0] — 2026-05-26 (yanked)

### Added

- Composite GitHub Action that posts a collapsible PR comment with
  normalized coupling scores for the changed files, classifying each
  pair as 🟢 / 🟡 / 🔴 against configurable thresholds.
- Co-change matrix engine over `git log --no-merges` with rename
  resolution, unicode-filename decoding (octal-escape form), binary
  extension filtering, and `fnmatch`-glob path exclusions.
- Normalized scoring: `score = co_count / max(file_a_commits, file_b_commits)`.
- Delta line on re-push: edits the existing comment in place with a
  `🟡 0.45 → 🔴 0.82` summary derived from a hidden JSON blob in the
  previous comment body.
- CODEOWNERS-aware reviewer suggestions: surfaces owners of coupled
  files who are not already on the PR.
- `fail_threshold` input (`low` / `medium` / `high`) for opt-in CI
  failure when the PR coupling density crosses a configured floor.
- `publish_dashboard` mode: writes `coupling-history.json`,
  `coupling-dashboard.html` (Chart.js trend graph), and
  `coupling-score.json` (shields.io endpoint badge).
- GitLab CI support: detects `CI_SERVER_URL` and posts an MR note
  via `python-gitlab` with the same algorithm.
- Local CLI: `couplingguard --repo . --dry-run` prints the rendered
  comment without trying to reach an API.
- All eight error codes (E001–E008) from the PRD surface as exact
  user-facing messages with the documented exit codes.
- 158-test suite covering all modules: unit (pure-function), integration
  (mocked PyGithub / python-gitlab), and E2E (real-repo + fake event
  payload). 86% line coverage, mypy strict-clean, ruff clean.
