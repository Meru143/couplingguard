# 2026-05-26 — couplingguard PRD

## Section 1 — Project Overview

**Name:** couplingguard  
**Type:** GitHub Action + Python CLI library  
**Language:** Python 3.11+  
**License:** MIT (Action) / Dual-license (analytics library: MIT for OSS, commercial for private orgs)  
**Description:** couplingguard detects file coupling risk in pull requests by analyzing co-change frequency from git history. It posts a collapsible HTML comment on every PR showing the top coupled file pairs involving the PR's changed files, with optional CI failure above a configurable threshold. v1 adds GitLab MR support, CODEOWNERS-based reviewer suggestions, a shields.io README badge, a self-hosted historical trend dashboard, delta comments on re-push, and path exclusions.

---

## Section 2 — Problem Statement

- **No free CI-integrated coupling detector exists.** CodeScene's PR risk comments require a paid subscription ($1k+/month). Zero free GitHub Actions on the Marketplace detect co-change coupling.
- **AI coding agents land large PRs.** Copilot, Claude Code, and Cursor generate commits touching 10–30 files simultaneously. Coupling risk has never been higher or harder to see in code review.
- **Post-hoc analysis tools don't prevent coupling.** code-maat and similar tools analyze history after damage is done. The leverage point is at PR open time, before merge.
- **Raw coupling signal is noisy.** Single co-occurrences are noise. Normalized frequency across repo history is the real signal. No existing free tool applies normalization correctly.
- **CODEOWNERS doesn't signal coupling risk.** It assigns reviewers by file ownership but has no concept of which file pairs historically break together.
- **Monorepo teams have no coupling budget.** Without a threshold gate in CI, coupling entropy compounds silently for months until a post-mortem surfaces it.

---

## Section 3 — Solution

1. **Free, Marketplace-distributed GitHub Action** — install in 5 lines of YAML, no signup, no hosted service required.
2. **Normalized co-change scoring** — `score = co_changes / max(file_a_total_changes, file_b_total_changes)` produces a 0–1 ratio that is comparable across repos of any size and age.
3. **PR-time comment** — collapible HTML table posted to every PR showing top coupled pairs involving changed files, with risk badge (🟢/🟡/🔴).
4. **Optional CI failure gate** — `fail_threshold` input lets teams enforce a coupling budget without mandatory failure for all repos.
5. **CODEOWNERS reviewer suggestions** — when a coupling cluster is detected, surfaces the owners of the coupled files not in the PR as suggested reviewers.
6. **Delta comment** — on subsequent pushes to the same PR, edits the existing comment to show score change (`0.45 → 0.72`), not a fresh wall of text.
7. **Self-hosted trend dashboard** — static HTML artifact committed to the repo after each run, Chart.js visualization of per-file coupling score over time.
8. **GitLab CI support** — same algorithm, posts MR note via `python-gitlab`.

---

## Section 4 — Target Users

| User | Workflow improved |
|------|------------------|
| Platform engineers at monorepo companies | Replace tribal knowledge about "files that always break together" with a quantified, CI-enforced coupling budget |
| Senior engineers reviewing PRs | Immediately see which files in a PR have historically caused regressions in unrelated modules |
| DevOps teams adopting AI coding agents | Detect AI-agent-generated PRs that touch files with high coupling density |
| Open-source maintainers | Add a coupling-aware review step to PRs from external contributors |

---

## Section 5 — Tech Stack Table

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| Git history parsing | `GitPython` | `3.1.50` | Walk commit log, extract per-commit file lists |
| GitHub API | `PyGithub` | `2.9.1` | Post/edit PR issue comments, check PRs, set commit status |
| GitLab API | `python-gitlab` | `4.13.0` | Post/edit MR notes for GitLab CI support |
| CODEOWNERS parsing | `codeowners` | `0.7.0` | Map changed files to owners via `CodeOwners.of(path)` |
| Config file | `PyYAML` | `6.0.2` | Parse `.couplingguard.yml` |
| Path glob matching | `fnmatch` (stdlib) | — | Exclude path pattern matching |
| Testing | `pytest` | `9.0.3` | Unit and integration tests |
| Test coverage | `pytest-cov` | `6.1.0` | Coverage reporting |
| Linting | `ruff` | `0.11.x` | Fast Python linter replacing flake8/isort |
| Type checking | `mypy` | `1.15.x` | Static typing |
| Release tooling | `python-semantic-release` | `9.x` | Automated versioning and changelog from commits |
| Badge generation | `shields.io` endpoint badge | — | README coupling score badge via URL |
| Trend dashboard | Chart.js via CDN | `4.x` | Embedded in static HTML artifact |

**Why GitPython over pygit2?**
pygit2 is faster for large repos but requires compiled libgit2 binaries, which adds cross-platform complexity in GitHub Actions runners. GitPython is pure Python, ships on all runners with `pip install`, and is fast enough for 90-day git log analysis (sub-second on any repo with <100k commits).

**Why PyGithub over raw `requests` calls to GitHub API?**
PyGithub wraps auth, pagination, and rate-limit handling. `pr.create_issue_comment(body)` and `pr.get_issue_comments()` are the only two API surfaces needed — PyGithub makes both trivial and handles retries.

**Why composite action (not Docker)?**
Composite actions run directly on the runner — no Docker image build, no cross-platform compilation, no multi-minute startup. Python is available on all GitHub-hosted runners. The Action installs deps via `pip` in one step, which is cached between runs.

---

## Section 6 — Core Features (v1)

### 1. Co-Change Matrix Engine
- Parse `git log --stat --since=<lookback_days>d --follow` via `GitPython`
- Build in-memory dict of dicts: `co_change_matrix[file_a][file_b] = count`
- Track per-file total commit count: `file_commit_count[file] = count`
- Apply `min_occurrences` filter: drop pairs with `co_change_matrix[a][b] < min_occurrences`
- Apply exclude path patterns from `.couplingguard.yml` before matrix construction
- Normalize: `score = co_change_matrix[a][b] / max(file_commit_count[a], file_commit_count[b])`

### 2. PR Coupling Analysis
- Retrieve PR changed files from `GITHUB_EVENT_PATH` (no API call needed — already in the event payload)
- Find all pairs `(pr_file, any_file)` where `any_file` appears in the co-change matrix for `pr_file`
- Sort by normalized score descending, take top `max_pairs` (default 10)
- Classify each pair: 🟢 score < `low_threshold` (0.3), 🟡 < `high_threshold` (0.7), 🔴 >= `high_threshold`
- Compute PR-level coupling density: `max score across all pairs in the PR`

### 3. PR Comment (GitHub)
- Find existing couplingguard comment via `pr.get_issue_comments()` filtered by HTML marker `<!-- couplingguard:marker -->`
- If no existing comment: `pr.create_issue_comment(body)` with full collapsible table
- If existing comment (delta mode): `comment.edit(new_body)` with score delta line prepended: `Score changed: 🟡 0.45 → 🔴 0.72`
- Comment format: `<details><summary>🔍 couplingguard — N pairs, highest risk: 🔴 0.82</summary>...table...</details>`
- Table columns: `| File in PR | Coupled With | Score | Risk | Co-changes |`

### 4. CI Failure Gate
- If `fail_threshold` input is set (`low`, `medium`, `high`) and PR coupling density exceeds threshold level, exit with code 1
- Print a clear message to Actions log: `couplingguard: PR coupling density 0.82 exceeds fail_threshold=high (0.7). Failing check.`
- If `fail_threshold` not set: always exit 0 regardless of score

### 5. CODEOWNERS Reviewer Suggestions
- Load `CODEOWNERS` file via `codeowners.CodeOwners(text)`
- For each `(pr_file, coupled_file)` pair: call `owners.of(coupled_file)` to get owners of the coupled file NOT in the PR
- Deduplicate suggested reviewers across all pairs
- Append to PR comment: `**Suggested reviewers for coupled files:** @team-infra, @alice`

### 6. Delta Comment
- Store previous run's per-file scores in PR comment HTML as a hidden JSON blob: `<!-- couplingguard:data:{"scores":{"src/payment.py":0.45}} -->`
- On next run: parse JSON from existing comment, compute delta per file, prepend delta summary

### 7. Self-Hosted Trend Dashboard
- After each run: append to `coupling-history.json` in repo root (read from existing file or create new)
- Format: `[{"date": "2026-05-26", "pr": 142, "max_score": 0.82, "pairs": [...]}]`
- Generate `coupling-dashboard.html` via string template with embedded Chart.js CDN link
- Upload as GitHub Actions artifact via `actions/upload-artifact` step in the composite action
- Optional: commit dashboard HTML to `gh-pages` branch if `publish_dashboard: true` input is set

### 8. GitLab CI Support
- Detect GitLab environment via `CI_SERVER_URL`, `CI_PROJECT_ID`, `CI_MERGE_REQUEST_IID` env vars
- Authenticate via `python-gitlab`: `gl = gitlab.Gitlab(CI_SERVER_URL, private_token=GITLAB_TOKEN)`
- Get MR: `project.mergerequests.get(CI_MERGE_REQUEST_IID)`
- Post note: `mr.notes.create({"body": comment_body})`
- Find existing note: iterate `mr.notes.list()` and filter by `<!-- couplingguard:marker -->` in body

### 9. Path Exclusions
- `.couplingguard.yml` config file (optional, repo root):
```yaml
exclude:
  - "docs/**"
  - "*.md"
  - "migrations/**"
lookback_days: 90
min_occurrences: 3
max_pairs: 10
low_threshold: 0.3
high_threshold: 0.7
fail_threshold: null  # or "low" | "medium" | "high"
publish_dashboard: false
```
- Patterns matched via `fnmatch.fnmatch(path, pattern)` for each exclude pattern
- Config loaded at startup; Action inputs override config file values

### 10. Safety Features
- Never writes to the git working tree (all output is via GitHub/GitLab API or Action artifacts)
- Dry-run mode: `dry_run: true` input prints comment body to stdout without posting
- Handles repos with no git history (< `min_occurrences` commits): posts informational comment instead of failing
- Handles missing CODEOWNERS file gracefully (reviewer suggestions silently skipped)
- Rate limit awareness: PyGithub raises `RateLimitExceededException`; catch and retry after `reset_timestamp`

---

## Section 7 — Interface Spec

### action.yml Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `github_token` | string | `${{ github.token }}` | GitHub token for posting comments |
| `gitlab_token` | string | `""` | GitLab personal access token (GitLab CI only) |
| `lookback_days` | number | `90` | Days of git history to analyze |
| `min_occurrences` | number | `3` | Min co-change count to include a pair |
| `max_pairs` | number | `10` | Max pairs to show in comment |
| `low_threshold` | number | `0.3` | Score below this is 🟢 Low |
| `high_threshold` | number | `0.7` | Score above this is 🔴 High |
| `fail_threshold` | string | `""` | Fail CI if max score exceeds: `low`, `medium`, or `high` |
| `exclude` | string | `""` | Newline-separated glob patterns to exclude |
| `publish_dashboard` | boolean | `false` | Commit dashboard HTML to gh-pages |
| `dry_run` | boolean | `false` | Print comment to stdout without posting |

### Workflow YAML — Minimal Installation

```yaml
name: Coupling Guard
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  coupling:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # required for full git history
      - uses: your-org/couplingguard@v1
        with:
          github_token: ${{ github.token }}
```

### Workflow YAML — Full Configuration

```yaml
- uses: your-org/couplingguard@v1
  with:
    github_token: ${{ github.token }}
    lookback_days: 180
    min_occurrences: 5
    max_pairs: 15
    low_threshold: 0.25
    high_threshold: 0.65
    fail_threshold: high
    exclude: |
      docs/**
      *.md
      migrations/**
    publish_dashboard: true
```

### PR Comment HTML Structure

```html
<!-- couplingguard:marker -->
<!-- couplingguard:data:{"max_score":0.82,"scores":{"src/payment.py":0.82}} -->
<details>
<summary>🔍 couplingguard — 5 pairs detected, highest risk: 🔴 0.82</summary>

> ⚠️ Score changed since last push: 🟡 0.45 → 🔴 0.82 (src/payment.py)

| File in PR | Coupled With | Score | Risk | Co-changes |
|------------|-------------|-------|------|-----------|
| `src/payment.py` | `src/billing.py` | 0.82 | 🔴 High | 41/50 commits |
| `src/payment.py` | `tests/test_billing.py` | 0.64 | 🟡 Medium | 32/50 commits |

**Suggested reviewers for coupled files:** @team-payments, @alice

</details>
```

---

## Section 8 — Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    GitHub Actions Runner                      │
│                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐   │
│  │  actions/        │     │  .couplingguard.yml           │   │
│  │  checkout@v4     │     │  (optional config)            │   │
│  │  fetch-depth: 0  │     └──────────────┬───────────────┘   │
│  └────────┬────────┘                     │                   │
│           │ $GITHUB_WORKSPACE             │ load config       │
│           ▼                              ▼                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ConfigLoader                            │    │
│  │  merge(action inputs, .couplingguard.yml, defaults) │    │
│  └──────────────────────────┬──────────────────────────┘    │
│                             │ Config                         │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              GitHistoryParser (GitPython)             │   │
│  │  repo.iter_commits(since=lookback_days)               │   │
│  │  commit.stats.files → per-commit file list            │   │
│  │  apply exclude patterns (fnmatch)                     │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                             │ commit file lists              │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CoChangeMatrixBuilder                    │   │
│  │  co_change_matrix[a][b] += 1 (per commit pair)        │   │
│  │  file_commit_count[f] += 1                            │   │
│  │  filter: drop pairs < min_occurrences                 │   │
│  │  normalize: score = co / max(count_a, count_b)        │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                             │ scored pairs                   │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              PRAnalyzer                               │   │
│  │  load PR files from $GITHUB_EVENT_PATH                │   │
│  │  filter matrix: keep pairs involving PR files         │   │
│  │  sort by score desc, take top max_pairs               │   │
│  │  classify: 🟢 / 🟡 / 🔴                              │   │
│  └──────────┬─────────────────────────┬─────────────────┘   │
│             │ pairs                   │ pairs                │
│             ▼                         ▼                      │
│  ┌──────────────────┐      ┌──────────────────────────┐     │
│  │  CODEOWNERSLoader│      │  DeltaExtractor           │     │
│  │  CodeOwners.of() │      │  parse hidden JSON from   │     │
│  │  suggest owners  │      │  existing PR comment      │     │
│  └────────┬─────────┘      └──────────┬───────────────┘     │
│           │ suggested owners          │ previous scores      │
│           └────────────┬─────────────┘                      │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CommentRenderer                          │   │
│  │  build collapsible HTML comment                       │   │
│  │  embed hidden JSON data blob                          │   │
│  │  prepend delta line if previous scores exist          │   │
│  └──────────┬──────────────────────────┬────────────────┘   │
│             │ comment body             │ comment body        │
│             ▼                          ▼                     │
│  ┌────────────────────┐    ┌───────────────────────────┐   │
│  │  GitHubPoster      │    │  DashboardWriter           │   │
│  │  (PyGithub)        │    │  append coupling-history   │   │
│  │  create or edit    │    │  .json                     │   │
│  │  PR issue comment  │    │  generate HTML + Chart.js  │   │
│  │                    │    │  upload as artifact        │   │
│  │  set commit status │    └───────────────────────────┘   │
│  │  if fail_threshold │                                     │
│  └────────────────────┘                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Section 9 — Architecture / Package Structure

```
couplingguard/
├── action.yml                    # Composite action definition — inputs, steps
├── pyproject.toml                # Package metadata, deps, ruff/mypy config
├── README.md                     # Install instructions, usage, badge
├── CHANGELOG.md
├── LICENSE
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                # Lint, test, coverage on push/PR
│   │   └── release.yml           # python-semantic-release on tag
│   └── CODEOWNERS
├── src/
│   └── couplingguard/
│       ├── __init__.py           # Public API: analyze(), run()
│       ├── cli.py                # Entrypoint for local CLI usage (argparse)
│       ├── config.py             # ConfigLoader: merge YAML + action inputs + defaults
│       ├── git_parser.py         # GitHistoryParser: GitPython commit walk
│       ├── matrix.py             # CoChangeMatrixBuilder: build, filter, normalize
│       ├── pr_analyzer.py        # PRAnalyzer: filter matrix by PR files, classify
│       ├── codeowners_loader.py  # CODEOWNERSLoader: parse + suggest reviewers
│       ├── delta.py              # DeltaExtractor: parse hidden JSON from comment
│       ├── renderer.py           # CommentRenderer: build HTML comment string
│       ├── github_poster.py      # GitHubPoster: PyGithub create/edit comment
│       ├── gitlab_poster.py      # GitLabPoster: python-gitlab MR notes
│       ├── dashboard.py          # DashboardWriter: JSON history + HTML generation
│       └── models.py             # Dataclasses: CouplingPair, Config, PRAnalysis
└── tests/
    ├── conftest.py               # Fixtures: fake repo, fake PR event payload
    ├── test_git_parser.py        # Unit: commit walk, file extraction
    ├── test_matrix.py            # Unit: co-change counting, normalization, filtering
    ├── test_pr_analyzer.py       # Unit: PR file filtering, classification, sorting
    ├── test_config.py            # Unit: config loading, merging, defaults
    ├── test_renderer.py          # Unit: HTML output, delta line, marker presence
    ├── test_codeowners_loader.py # Unit: owner lookup per file path
    ├── test_delta.py             # Unit: JSON extraction from HTML comment
    ├── test_dashboard.py         # Unit: JSON append, HTML generation
    └── integration/
        ├── test_github_poster.py # Integration: mock PyGithub, verify API calls
        └── test_gitlab_poster.py # Integration: mock python-gitlab, verify API calls
```

### Key Types (models.py)

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    lookback_days: int = 90
    min_occurrences: int = 3
    max_pairs: int = 10
    low_threshold: float = 0.3
    high_threshold: float = 0.7
    fail_threshold: Optional[str] = None   # "low" | "medium" | "high" | None
    exclude: list[str] = field(default_factory=list)
    dry_run: bool = False
    publish_dashboard: bool = False

@dataclass
class CouplingPair:
    file_in_pr: str
    coupled_file: str
    score: float          # normalized 0-1
    co_changes: int       # raw co-change count
    total_commits: int    # max(file_a_commits, file_b_commits)
    risk: str             # "low" | "medium" | "high"
    suggested_owners: list[str] = field(default_factory=list)

@dataclass
class PRAnalysis:
    pr_number: int
    pr_files: list[str]
    pairs: list[CouplingPair]
    max_score: float
    pr_risk: str
    previous_max_score: Optional[float] = None
```

---

## Section 10 — Error Handling

| Code | Scenario | User-facing message | Action |
|------|----------|--------------------|-|
| `E001` | `fetch-depth` is not 0 — shallow clone | `couplingguard: Error — repository is a shallow clone. Add 'fetch-depth: 0' to your checkout step.` | Exit 1 |
| `E002` | Repo has fewer commits than `min_occurrences` | `couplingguard: Warning — not enough history (<N commits in lookback window). Posting informational comment.` | Post comment, exit 0 |
| `E003` | `GITHUB_TOKEN` missing or lacks `pull-requests: write` | `couplingguard: Error — could not post PR comment. Verify 'permissions: pull-requests: write' is set.` | Exit 1 |
| `E004` | CODEOWNERS file not found | `couplingguard: Info — CODEOWNERS not found. Reviewer suggestions skipped.` | Continue silently |
| `E005` | `.couplingguard.yml` exists but has invalid YAML | `couplingguard: Error — .couplingguard.yml is not valid YAML. Line N: <yaml error>` | Exit 1 |
| `E006` | GitHub API rate limit hit | `couplingguard: Warning — GitHub API rate limit hit. Retrying after <timestamp>.` | Sleep + retry once |
| `E007` | `fail_threshold` set and PR coupling density exceeds it | `couplingguard: PR coupling density <score> exceeds fail_threshold=<level> (<value>). Failing check.` | Exit 1 |
| `E008` | GitLab token missing in GitLab CI environment | `couplingguard: Error — GITLAB_TOKEN not set. Cannot post MR note.` | Exit 1 |

---

## Section 11 — Edge Cases

1. **Merge commits** — `git log --no-merges` must be used; merge commits inflate co-change counts for all files that diverged and converged.
2. **Renames** — `--follow` flag in `git log` only works per file. When using `--stat`, track renames by detecting `{old => new}` patterns in stat output and mapping old path to new path throughout history.
3. **Binary files** — `git log --stat` includes binary files. Filter out common binary extensions (`.png`, `.jpg`, `.lock`, `.whl`) before matrix construction.
4. **Repos with no commits in lookback window** — empty git log output must not crash the matrix builder; return empty matrix and post informational comment.
5. **PRs with 0 changed files** — GitHub API can return empty file list for certain PR types; handle gracefully with "no files to analyze" comment.
6. **Very large PRs (500+ files)** — building all pairs for a 500-file PR is O(500 * matrix_size). Cap PR file count at 200 and warn user in comment.
7. **Monorepos with 50k+ commits** — GitPython `iter_commits(since=...)` can be slow. Use `--format="%H"` with `--name-only` via subprocess for repos >10k commits in the window; benchmark threshold in CI.
8. **CODEOWNERS with email entries** — `codeowners` library returns `('EMAIL', 'user@example.com')` tuples. Handle both `USERNAME` and `EMAIL` types in suggestion rendering.
9. **Unicode filenames** — git encodes non-ASCII filenames with surrounding quotes and octal escapes. Decode these before path matching.
10. **Delta JSON parsing failure** — if the hidden JSON blob in the previous comment is malformed (e.g., comment was manually edited), catch `json.JSONDecodeError` and proceed without delta, logging a warning.
11. **PR comment exceeds GitHub's 65536-character limit** — truncate the pairs table to fit and append "... and N more pairs. Run couplingguard locally for full report."

---

## Section 12 — Testing Strategy

### Unit Tests
- **git_parser.py** — mock `GitPython.Repo` with in-memory commit fixtures; test `since` filtering, `--no-merges`, rename handling, binary file exclusion
- **matrix.py** — test co-change counting with known commit sequences; test normalization formula; test `min_occurrences` filter; test exclude pattern matching
- **pr_analyzer.py** — test pair filtering for PR files; test `max_pairs` truncation; test risk classification at boundary values (0.3, 0.7)
- **config.py** — test YAML loading, action input override, default values, invalid YAML error
- **renderer.py** — test HTML marker presence, delta line rendering, hidden JSON blob embedding, table row count
- **delta.py** — test JSON extraction regex, malformed JSON handling
- **codeowners_loader.py** — test `CodeOwners.of()` for USERNAME and EMAIL types, missing CODEOWNERS file

### Integration Tests
- **github_poster.py** — mock `PyGithub.Github`, `repo.get_pull()`, `pr.create_issue_comment()`, `pr.get_issue_comments()`, `comment.edit()`. Verify: correct comment body is posted; existing comment is edited not duplicated; `fail_threshold` triggers exit 1.
- **gitlab_poster.py** — mock `python-gitlab` Gitlab instance; verify `mr.notes.create()` called with correct body; verify existing note found and updated.

### Mocking Approach
- `unittest.mock.patch` for all external API calls
- `tmp_path` pytest fixture for creating real git repos with `git.Repo.init()` + scripted commits for integration of the git parser layer

---

## Section 13 — Distribution

### Build Commands
```bash
# Install for local dev
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=src/couplingguard --cov-report=term-missing

# Lint
ruff check src/ tests/
mypy src/
```

### Action Installation (users)
```yaml
- uses: your-org/couplingguard@v1
```
Tag-pinned. `v1` is a moving major-version tag updated on every minor/patch release via `python-semantic-release`.

### PyPI (CLI)
```bash
pip install couplingguard
couplingguard --repo . --lookback-days 90
```

### Release Pipeline
- `python-semantic-release` reads conventional commits (`feat:`, `fix:`, `BREAKING CHANGE:`) and bumps version in `pyproject.toml`
- GitHub Actions release workflow: tag trigger → `semantic-release publish` → PyPI upload via Trusted Publishing → update `v1` major-version tag

---

## Section 14 — Differentiators

1. **vs CodeScene** — Free, open-source, runs entirely in CI without an external service. CodeScene costs $1k+/month.
2. **vs code-maat** — Java 2016 CLI toy, unmaintained, no GitHub Action, no normalization, no visualization. couplingguard is a maintained Python Action with normalized scoring and live PR comments.
3. **vs Danger.js** — Danger.js is a framework requiring custom scripts; it provides no coupling analysis. couplingguard is a zero-config plug-and-play Action.
4. **vs CODEOWNERS** — CODEOWNERS assigns reviewers by static file ownership; couplingguard surfaces dynamic co-change risk. Complementary, not competing — couplingguard uses CODEOWNERS to suggest better reviewers.

---

## Section 15 — Future Scope (v2+)

- [ ] GitLab self-managed instance support (custom `gitlab_url` input)
- [ ] Bitbucket PR comment support via Bitbucket REST API
- [ ] Configurable reviewer auto-request (not just suggestion — actually request the reviewer via GitHub API)
- [ ] Coupling cluster visualization (D3 force graph in dashboard HTML)
- [ ] Hosted SaaS dashboard: $29/month per org, persistent history across repos
- [ ] Jira/Linear ticket linking: surface coupling risk in linked tickets
- [ ] Language-aware coupling exclusion (e.g., ignore test files coupling with their source file)
- [ ] GitHub Marketplace Pro tier: `$5/month` per private repo for advanced analytics

---

## Section 16 — Success Metrics

- [ ] Action completes in < 30 seconds for a repo with 90 days of history and < 10k commits
- [ ] Zero false failures due to missing `fetch-depth: 0` — detected and surfaced as actionable error
- [ ] PR comment posted on every PR event type: `opened`, `synchronize`, `reopened`
- [ ] Delta comment correctly detects and edits existing comment on `synchronize` event
- [ ] Unit test coverage ≥ 80% (`pytest-cov`)
- [ ] mypy passes with `--strict` on all `src/` files
- [ ] Runs on `ubuntu-latest`, `macos-latest`, `windows-latest` GitHub-hosted runners
- [ ] README badge renders correctly on GitHub within 60 seconds of a merged PR

---

## Section 17 — Additional Deliverables

### Documentation Files
- [ ] `README.md` — install snippet, inputs table, PR comment screenshot, badge example
- [ ] `CONTRIBUTING.md` — local dev setup, test commands, commit message conventions
- [ ] `CODE_OF_CONDUCT.md` — Contributor Covenant
- [ ] `SECURITY.md` — vulnerability disclosure contact
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md`
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`

### Development Environment
- [ ] `devcontainer/devcontainer.json` — Python 3.11, ruff, mypy, pytest
- [ ] `.env.example` — `GITHUB_TOKEN=`, `GITLAB_TOKEN=`

### Logging & Observability
- [ ] Structured log output via Python `logging` to Actions step log
- [ ] Log levels: DEBUG (matrix stats), INFO (pairs found, comment posted), WARNING (edge cases), ERROR (fatal)
- [ ] `COUPLINGGUARD_DEBUG=1` env var enables DEBUG level

### Environment Variables (runtime)
| Variable | Purpose | Default |
|----------|---------|---------|
| `GITHUB_TOKEN` | GitHub API auth (auto-injected in Actions) | — |
| `GITLAB_TOKEN` | GitLab API auth | — |
| `GITHUB_EVENT_PATH` | Path to PR event JSON payload (auto-injected) | — |
| `GITHUB_WORKSPACE` | Path to checked-out repo (auto-injected) | — |
| `COUPLINGGUARD_DEBUG` | Enable debug logging | `0` |

---

## Section 18 — Expanded Testing Strategy

### Unit Tests (target: 85% coverage)
- [ ] `test_git_parser.py`: shallow clone detection raises `ShallowCloneError`
- [ ] `test_git_parser.py`: commits outside lookback window excluded
- [ ] `test_git_parser.py`: merge commits excluded (`--no-merges`)
- [ ] `test_git_parser.py`: binary files (`.png`, `.jpg`) excluded from file lists
- [ ] `test_git_parser.py`: renamed files mapped to new path via rename detection
- [ ] `test_git_parser.py`: unicode filename decoded from octal escape
- [ ] `test_matrix.py`: co-change count correct for 3-file commit
- [ ] `test_matrix.py`: normalization: `score = co / max(count_a, count_b)`
- [ ] `test_matrix.py`: pairs below `min_occurrences` filtered out
- [ ] `test_matrix.py`: exclude glob `docs/**` removes matched files before matrix
- [ ] `test_matrix.py`: empty history returns empty matrix without exception
- [ ] `test_pr_analyzer.py`: only pairs involving PR files returned
- [ ] `test_pr_analyzer.py`: pairs sorted by score descending
- [ ] `test_pr_analyzer.py`: `max_pairs` truncation applied
- [ ] `test_pr_analyzer.py`: score 0.29 classified as "low"
- [ ] `test_pr_analyzer.py`: score 0.30 classified as "medium"
- [ ] `test_pr_analyzer.py`: score 0.70 classified as "high"
- [ ] `test_pr_analyzer.py`: 500-file PR capped at 200 with warning
- [ ] `test_config.py`: YAML file loaded and values set
- [ ] `test_config.py`: action input overrides YAML value
- [ ] `test_config.py`: missing YAML file uses defaults
- [ ] `test_config.py`: invalid YAML raises `ConfigError` with line number
- [ ] `test_renderer.py`: `<!-- couplingguard:marker -->` present in output
- [ ] `test_renderer.py`: hidden JSON blob contains `max_score`
- [ ] `test_renderer.py`: delta line rendered when `previous_max_score` set
- [ ] `test_renderer.py`: no delta line when no previous score
- [ ] `test_renderer.py`: table row count equals `len(pairs)`
- [ ] `test_renderer.py`: reviewer list rendered when suggested_owners non-empty
- [ ] `test_delta.py`: JSON extracted correctly from well-formed comment
- [ ] `test_delta.py`: `json.JSONDecodeError` caught; returns `None` gracefully
- [ ] `test_delta.py`: returns `None` when marker absent from comment
- [ ] `test_codeowners_loader.py`: USERNAME type owner returned for matched path
- [ ] `test_codeowners_loader.py`: EMAIL type owner returned for matched path
- [ ] `test_codeowners_loader.py`: missing CODEOWNERS file returns empty list
- [ ] `test_dashboard.py`: JSON appended to existing history file
- [ ] `test_dashboard.py`: new history file created when none exists
- [ ] `test_dashboard.py`: HTML output contains `Chart.js` CDN script tag

### Integration Tests
- [ ] `test_github_poster.py`: `pr.create_issue_comment()` called with correct body on first run
- [ ] `test_github_poster.py`: `comment.edit()` called (not `create_issue_comment`) on second run with existing marker
- [ ] `test_github_poster.py`: `RateLimitExceededException` triggers retry with sleep
- [ ] `test_github_poster.py`: `fail_threshold=high` with score 0.82 → exit code 1
- [ ] `test_github_poster.py`: `fail_threshold` not set with score 0.82 → exit code 0
- [ ] `test_github_poster.py`: `dry_run=True` → `create_issue_comment` never called
- [ ] `test_gitlab_poster.py`: `mr.notes.create()` called with correct body
- [ ] `test_gitlab_poster.py`: existing note found by marker and updated

### E2E Tests
- [ ] Full workflow: init git repo with scripted commits → run couplingguard → verify pairs match expected scores
- [ ] Full workflow: PR with 0 changed files → informational comment posted, exit 0
- [ ] Full workflow: repo with 1 commit → empty matrix → informational comment, exit 0

### Test Infrastructure
- [ ] `conftest.py`: `fake_repo` fixture using `git.Repo.init(tmp_path)` with scripted commits
- [ ] `conftest.py`: `fake_pr_event` fixture returning JSON payload with configurable `changed_files`
- [ ] `conftest.py`: `mock_github` fixture wrapping `unittest.mock.MagicMock` for PyGithub objects

---

## Section 19 — CI/CD Pipeline

### GitHub Actions — CI (`.github/workflows/ci.yml`)
- [ ] Trigger: `push` to `main`, `pull_request` to `main`
- [ ] Job: `lint` — `ruff check src/ tests/`
- [ ] Job: `type-check` — `mypy src/ --strict`
- [ ] Job: `test` — `pytest tests/ -v --cov=src/couplingguard --cov-report=xml`
- [ ] Job: `test` — matrix: `python-version: ["3.11", "3.12", "3.13"]`
- [ ] Job: `test` — matrix: `os: [ubuntu-latest, macos-latest, windows-latest]`
- [ ] Job: `coverage` — upload `coverage.xml` to Codecov

### GitHub Actions — Release (`.github/workflows/release.yml`)
- [ ] Trigger: push to `main` (semantic-release decides if version bump needed)
- [ ] Job: `release` — `python-semantic-release publish`
- [ ] Job: `release` — PyPI upload via Trusted Publishing (no API key stored)
- [ ] Job: `release` — update `v1` major-version tag to new commit

### Makefile Targets
- [ ] `make lint` — ruff check
- [ ] `make type-check` — mypy
- [ ] `make test` — pytest unit tests
- [ ] `make test-integration` — pytest integration/ only
- [ ] `make test-e2e` — pytest e2e/ only
- [ ] `make build` — `python -m build`
- [ ] `make dev` — `pip install -e ".[dev]"`

### Security & Quality
- [ ] `pip-audit` added to CI for dependency vulnerability scanning
- [ ] `ruff` configured with `select = ["E", "F", "I", "UP"]` in `pyproject.toml`
- [ ] `mypy` configured with `strict = true` in `pyproject.toml`
- [ ] Dependabot enabled for `pip` ecosystem in `.github/dependabot.yml`
