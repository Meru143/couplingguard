# 2026-05-26 — couplingguard TODO

<!--
Phase 0 — Active skills (resolved at session start, 2026-05-26):
The skills named in the original system prompt (architecture-patterns, error-handling-patterns,
git-commit, systematic-debugging, test-driven-development, devops-engineer) are NOT registered
in this Claude Code environment. None of them appear in /skills list, so they cannot be
invoked via the Skill tool. Their *patterns* are applied directly:

  * Conventional Commits for every commit (replaces git-commit skill)
  * Pure-function pipelines + railway error handling in run() (replaces architecture-patterns)
  * Custom CouplingGuardError subclasses + single catch boundary (replaces error-handling-patterns)
  * Happy-path-first, then edge cases for risky parsers (replaces systematic-debugging)
  * Test-first for renderer/matrix/delta; test against interface, not implementation
    (replaces test-driven-development)
  * Composite Action + ruff/mypy CI matrix (replaces devops-engineer)
-->

---

## Phase 1: Project Setup

### 1.1 Repository Initialization
- [ ] `git init couplingguard` and push to GitHub
- [ ] Create `README.md` with project name, one-line description, and install placeholder
- [ ] Create `LICENSE` file (MIT)
- [ ] Create `.gitignore` for Python: `__pycache__/`, `*.pyc`, `.coverage`, `dist/`, `.mypy_cache/`, `.ruff_cache/`
- [ ] Create `CHANGELOG.md` with initial `## [Unreleased]` section

### 1.2 Directory Structure
- [ ] Create `src/couplingguard/` package directory
- [ ] Create `src/couplingguard/__init__.py` with `__version__ = "0.1.0"`
- [ ] Create `src/couplingguard/models.py` (empty dataclass stubs)
- [ ] Create `src/couplingguard/config.py` (empty)
- [ ] Create `src/couplingguard/git_parser.py` (empty)
- [ ] Create `src/couplingguard/matrix.py` (empty)
- [ ] Create `src/couplingguard/pr_analyzer.py` (empty)
- [ ] Create `src/couplingguard/codeowners_loader.py` (empty)
- [ ] Create `src/couplingguard/delta.py` (empty)
- [ ] Create `src/couplingguard/renderer.py` (empty)
- [ ] Create `src/couplingguard/github_poster.py` (empty)
- [ ] Create `src/couplingguard/gitlab_poster.py` (empty)
- [ ] Create `src/couplingguard/dashboard.py` (empty)
- [ ] Create `src/couplingguard/cli.py` (empty)
- [ ] Create `tests/` directory with `__init__.py`
- [ ] Create `tests/conftest.py` (empty)
- [ ] Create `tests/integration/` directory with `__init__.py`
- [ ] Create `.github/workflows/` directory
- [ ] Create `.github/ISSUE_TEMPLATE/` directory
- [ ] Create `action.yml` (empty stub)

### 1.3 Package Metadata
- [ ] Create `pyproject.toml` with `[project]` table: `name = "couplingguard"`, `version = "0.1.0"`, `requires-python = ">=3.11"`
- [ ] Add `[project.dependencies]`: `GitPython>=3.1.50`, `PyGithub>=2.9.1`, `python-gitlab>=4.13.0`, `codeowners>=0.7.0`, `PyYAML>=6.0.2`
- [ ] Add `[project.optional-dependencies]` `dev`: `pytest>=9.0.3`, `pytest-cov>=6.1.0`, `ruff>=0.11`, `mypy>=1.15`
- [ ] Add `[project.scripts]`: `couplingguard = "couplingguard.cli:main"`
- [ ] Add `[tool.ruff]` config: `select = ["E", "F", "I", "UP"]`, `line-length = 100`
- [ ] Add `[tool.mypy]` config: `strict = true`, `python_version = "3.11"`
- [ ] Add `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "-v"`
- [ ] Add `[tool.coverage.run]`: `source = ["src/couplingguard"]`, `omit = ["tests/*"]`

### 1.4 Development Environment
- [ ] Create `.env.example`: `GITHUB_TOKEN=ghp_yourtoken`, `GITLAB_TOKEN=glpat_yourtoken`, `COUPLINGGUARD_DEBUG=0`
- [ ] Create `Makefile` with targets: `lint`, `type-check`, `test`, `test-integration`, `build`, `dev`
- [ ] Create `devcontainer/devcontainer.json` with Python 3.11 base image and `pip install -e ".[dev]"` postCreate command

### 1.5 CI Workflow
- [ ] Create `.github/workflows/ci.yml` with trigger: `push` to `main` and `pull_request` to `main`
- [ ] Add job `lint`: `ruff check src/ tests/`
- [ ] Add job `type-check`: `mypy src/ --strict`
- [ ] Add job `test`: matrix `python-version: ["3.11", "3.12", "3.13"]`, matrix `os: ["ubuntu-latest", "macos-latest", "windows-latest"]`
- [ ] Add step in `test` job: `pytest tests/ -v --cov=src/couplingguard --cov-report=xml`
- [ ] Add step: upload `coverage.xml` to Codecov via `codecov/codecov-action@v4`

### 1.6 Release Workflow
- [ ] Create `.github/workflows/release.yml` with trigger: `push` to `main`
- [ ] Add job `release`: `python-semantic-release publish`
- [ ] Configure Trusted Publishing for PyPI in `pyproject.toml` under `[tool.semantic_release]`
- [ ] Add post-release step: update `v1` major-version tag to new commit SHA

### 1.7 Community Files
- [ ] Create `CONTRIBUTING.md`: local dev setup (`make dev`), test commands (`make test`), commit convention (Conventional Commits)
- [ ] Create `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
- [ ] Create `SECURITY.md` with vulnerability disclosure email
- [ ] Create `.github/ISSUE_TEMPLATE/bug_report.md` with: steps to reproduce, expected/actual behavior, `action.yml` version
- [ ] Create `.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Create `.editorconfig`: `indent_style = space`, `indent_size = 4`, `end_of_line = lf`
- [ ] Create `.github/dependabot.yml`: `package-ecosystem: pip`, `schedule: weekly`

---

## Phase 2: Data Models

### 2.1 Config Dataclass (models.py)
- [ ] Define `@dataclass class Config` with field `lookback_days: int = 90`
- [ ] Add field `min_occurrences: int = 3`
- [ ] Add field `max_pairs: int = 10`
- [ ] Add field `low_threshold: float = 0.3`
- [ ] Add field `high_threshold: float = 0.7`
- [ ] Add field `fail_threshold: Optional[str] = None`
- [ ] Add field `exclude: list[str] = field(default_factory=list)`
- [ ] Add field `dry_run: bool = False`
- [ ] Add field `publish_dashboard: bool = False`

### 2.2 CouplingPair Dataclass (models.py)
- [ ] Define `@dataclass class CouplingPair` with field `file_in_pr: str`
- [ ] Add field `coupled_file: str`
- [ ] Add field `score: float`
- [ ] Add field `co_changes: int`
- [ ] Add field `total_commits: int`
- [ ] Add field `risk: str` (values: `"low"` | `"medium"` | `"high"`)
- [ ] Add field `suggested_owners: list[str] = field(default_factory=list)`

### 2.3 PRAnalysis Dataclass (models.py)
- [ ] Define `@dataclass class PRAnalysis` with field `pr_number: int`
- [ ] Add field `pr_files: list[str]`
- [ ] Add field `pairs: list[CouplingPair]`
- [ ] Add field `max_score: float`
- [ ] Add field `pr_risk: str`
- [ ] Add field `previous_max_score: Optional[float] = None`

### 2.4 Custom Exceptions (models.py)
- [ ] Define `class CouplingGuardError(Exception): pass`
- [ ] Define `class ShallowCloneError(CouplingGuardError): pass`
- [ ] Define `class ConfigError(CouplingGuardError): pass`
- [ ] Define `class GitHubAuthError(CouplingGuardError): pass`

---

## Phase 3: Config Loader

### 3.1 YAML Config Loading (config.py)
- [ ] Import `yaml`, `os`, `pathlib.Path`, `models.Config`, `models.ConfigError`
- [ ] Define `def load_config(repo_root: Path, action_inputs: dict) -> Config`
- [ ] In `load_config`: check for `.couplingguard.yml` at `repo_root / ".couplingguard.yml"`
- [ ] If YAML file exists: open and call `yaml.safe_load(f)` — catch `yaml.YAMLError` and raise `ConfigError` with line number from exception
- [ ] If YAML file missing: use empty dict as base
- [ ] Build `Config` object: YAML values as base, `action_inputs` override any matching key
- [ ] For `exclude` field: if action input is a newline-separated string, split on `\n` and strip empty lines; merge with YAML list
- [ ] Return validated `Config` object

### 3.2 Action Input Parsing (config.py)
- [ ] Define `def parse_action_inputs() -> dict` reading from `os.environ` using `INPUT_*` variable pattern (GitHub Actions convention: `INPUT_LOOKBACK_DAYS`, `INPUT_MIN_OCCURRENCES`, etc.)
- [ ] Cast `lookback_days`, `min_occurrences`, `max_pairs` to `int`; catch `ValueError` and raise `ConfigError`
- [ ] Cast `low_threshold`, `high_threshold` to `float`; catch `ValueError` and raise `ConfigError`
- [ ] Cast `dry_run`, `publish_dashboard` to `bool` by checking if env value is `"true"` (case-insensitive)
- [ ] Return only keys that are set (non-empty string) so they override YAML; omit empty inputs

---

## Phase 4: Git History Parser

### 4.1 Repo Initialization (git_parser.py)
- [ ] Import `git` from `GitPython`, `datetime`, `pathlib.Path`, `models.ShallowCloneError`
- [ ] Define `def open_repo(repo_path: Path) -> git.Repo`
- [ ] In `open_repo`: call `git.Repo(repo_path)` — wrap `git.exc.InvalidGitRepositoryError` and raise `CouplingGuardError`
- [ ] Check for shallow clone: `repo.git.rev_parse("--is-shallow-repository")` returns `"true"` → raise `ShallowCloneError` with message including fix instructions

### 4.2 Commit Walk (git_parser.py)
- [ ] Define `def get_commits(repo: git.Repo, lookback_days: int) -> list[list[str]]`
- [ ] Compute `since_date = datetime.now() - timedelta(days=lookback_days)` formatted as `"--since=YYYY-MM-DD"`
- [ ] Call `repo.iter_commits(rev="HEAD", no_merges=True, since=since_date.strftime("%Y-%m-%d"))`
- [ ] For each commit: extract changed files via `commit.stats.files.keys()`
- [ ] Apply rename detection: check for ` => ` pattern in filenames (git `{old => new}` format), resolve to new path
- [ ] Apply binary file filter: skip files whose extension is in `BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".whl", ".tar", ".zip", ".lock", ".bin"}`
- [ ] Apply unicode filename decoding: if filename starts with `"` and contains `\\`, unescape octal sequences via `bytes.fromhex`
- [ ] Return list of per-commit file lists (empty sublists filtered out)

### 4.3 Commit Count Per File (git_parser.py)
- [ ] Define `def get_file_commit_counts(commits: list[list[str]]) -> dict[str, int]`
- [ ] Iterate all commits; increment `counts[file]` for each file in each commit
- [ ] Return `counts` dict

### 4.4 Exclude Pattern Application (git_parser.py)
- [ ] Define `def apply_excludes(files: list[str], exclude_patterns: list[str]) -> list[str]`
- [ ] Import `fnmatch`
- [ ] For each file: if any pattern matches via `fnmatch.fnmatch(file, pattern)`, exclude it
- [ ] Return filtered list
- [ ] Call `apply_excludes` on each commit's file list before returning from `get_commits`

---

## Phase 5: Co-Change Matrix Builder

### 5.1 Matrix Construction (matrix.py)
- [ ] Import `collections.defaultdict`, `itertools.combinations`, `models.Config`
- [ ] Define `def build_co_change_matrix(commits: list[list[str]]) -> tuple[dict, dict]`
- [ ] Initialize `co_change: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))`
- [ ] Initialize `file_counts: dict[str, int] = defaultdict(int)`
- [ ] For each commit file list: increment `file_counts[f]` for each file
- [ ] For each commit: generate all 2-combinations via `itertools.combinations(sorted(files), 2)`
- [ ] For each pair `(a, b)`: increment `co_change[a][b]` and `co_change[b][a]` (symmetric)
- [ ] Return `(co_change, file_counts)`

### 5.2 Min Occurrences Filter (matrix.py)
- [ ] Define `def filter_by_min_occurrences(co_change: dict, min_occurrences: int) -> dict`
- [ ] For each pair `(a, b)`: if `co_change[a][b] < min_occurrences`, remove from matrix
- [ ] Return filtered matrix (rebuild as plain dict, not defaultdict)

### 5.3 Normalization (matrix.py)
- [ ] Define `def normalize_pair(co_count: int, count_a: int, count_b: int) -> float`
- [ ] Return `co_count / max(count_a, count_b)` — handle `max == 0` by returning `0.0`
- [ ] Round result to 4 decimal places

### 5.4 Full Matrix Pipeline (matrix.py)
- [ ] Define `def build_normalized_matrix(commits: list[list[str]], config: Config) -> dict[tuple[str, str], tuple[float, int, int]]`
- [ ] Call `build_co_change_matrix(commits)` → `(co_change, file_counts)`
- [ ] Call `filter_by_min_occurrences(co_change, config.min_occurrences)`
- [ ] For each remaining pair: compute normalized score
- [ ] Return dict mapping `(file_a, file_b)` → `(score, co_count, max_total_commits)`

---

## Phase 6: PR Analyzer

### 6.1 PR File Loading (pr_analyzer.py)
- [ ] Import `json`, `os`, `pathlib.Path`, `models.PRAnalysis`, `models.CouplingPair`, `models.Config`
- [ ] Define `def load_pr_files() -> tuple[int, list[str]]`
- [ ] Read `os.environ["GITHUB_EVENT_PATH"]` → load JSON → extract `pull_request.number` and `pull_request.changed_files`
- [ ] If `changed_files` not in payload (some PR types): return empty list and log `INFO`
- [ ] Cap PR file list at 200 files; if exceeded, log warning to stdout

### 6.2 Pair Filtering (pr_analyzer.py)
- [ ] Define `def find_coupling_pairs(pr_files: list[str], matrix: dict, file_counts: dict, config: Config) -> list[CouplingPair]`
- [ ] For each `pr_file` in `pr_files`: look up all pairs in `matrix` where `pr_file` is either member
- [ ] Deduplicate: if pair `(a, b)` already added as `(b, a)`, skip
- [ ] For each pair: create `CouplingPair` with `file_in_pr`, `coupled_file`, `score`, `co_changes`, `total_commits`
- [ ] Classify risk: score < `config.low_threshold` → `"low"`, < `config.high_threshold` → `"medium"`, else `"high"`
- [ ] Sort by `score` descending
- [ ] Truncate to `config.max_pairs`
- [ ] Return list of `CouplingPair`

### 6.3 PR Analysis Assembly (pr_analyzer.py)
- [ ] Define `def analyze_pr(pr_files: list[str], matrix: dict, file_counts: dict, config: Config) -> PRAnalysis`
- [ ] Call `find_coupling_pairs`
- [ ] Compute `max_score = max(p.score for p in pairs) if pairs else 0.0`
- [ ] Classify PR-level risk using same thresholds as pair classification
- [ ] Return `PRAnalysis(pr_number, pr_files, pairs, max_score, pr_risk)`

---

## Phase 7: CODEOWNERS Loader

### 7.1 CODEOWNERS File Loading (codeowners_loader.py)
- [ ] Import `pathlib.Path`, `codeowners.CodeOwners`
- [ ] Define `CODEOWNERS_SEARCH_PATHS = [".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"]`
- [ ] Define `def load_codeowners(repo_root: Path) -> Optional[CodeOwners]`
- [ ] Try each path in `CODEOWNERS_SEARCH_PATHS`; if found: read text and return `CodeOwners(text)`
- [ ] If none found: log `INFO` message and return `None`

### 7.2 Owner Lookup (codeowners_loader.py)
- [ ] Define `def get_owners(codeowners: CodeOwners, file_path: str) -> list[str]`
- [ ] Call `codeowners.of(file_path)` → returns list of `(type, owner)` tuples
- [ ] Extract owner string for both `"USERNAME"` type (`@username`) and `"EMAIL"` type (email string)
- [ ] Return list of owner strings

### 7.3 Reviewer Suggestion (codeowners_loader.py)
- [ ] Define `def suggest_reviewers(pairs: list[CouplingPair], codeowners: Optional[CodeOwners], pr_files: list[str]) -> list[str]`
- [ ] If `codeowners is None`: return `[]`
- [ ] For each pair: call `get_owners(codeowners, pair.coupled_file)`
- [ ] Remove owners who are already listed in CODEOWNERS for `pr_files` (they're already involved)
- [ ] Deduplicate via `set`, preserve insertion order via `dict.fromkeys`
- [ ] Attach `suggested_owners` to each `CouplingPair` in-place
- [ ] Return flat deduplicated list of all suggested reviewers

---

## Phase 8: Delta Extractor

### 8.1 Hidden JSON Extraction (delta.py)
- [ ] Import `re`, `json`, `typing.Optional`
- [ ] Define `DELTA_MARKER_PATTERN = re.compile(r'<!-- couplingguard:data:({.*?}) -->', re.DOTALL)`
- [ ] Define `def extract_previous_data(comment_body: str) -> Optional[dict]`
- [ ] Apply `DELTA_MARKER_PATTERN.search(comment_body)` to find JSON blob
- [ ] If match found: `json.loads(match.group(1))` — catch `json.JSONDecodeError` and return `None` with WARNING log
- [ ] If no match: return `None`

### 8.2 Previous Score Extraction (delta.py)
- [ ] Define `def get_previous_max_score(comment_body: str) -> Optional[float]`
- [ ] Call `extract_previous_data(comment_body)`
- [ ] If data: return `data.get("max_score")` cast to `float`
- [ ] If None: return `None`

---

## Phase 9: Comment Renderer

### 9.1 Risk Emoji Helper (renderer.py)
- [ ] Define `RISK_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🔴"}`
- [ ] Define `def risk_emoji(risk: str) -> str`: return `RISK_EMOJI.get(risk, "⚪")`

### 9.2 Table Row Builder (renderer.py)
- [ ] Define `def render_table_row(pair: CouplingPair) -> str`
- [ ] Return markdown table row: `| \`{pair.file_in_pr}\` | \`{pair.coupled_file}\` | {pair.score:.2f} | {emoji} {pair.risk.title()} | {pair.co_changes}/{pair.total_commits} |`

### 9.3 Full Comment Body Builder (renderer.py)
- [ ] Import `json`, `models.PRAnalysis`, `models.Config`
- [ ] Define `def render_comment(analysis: PRAnalysis, config: Config) -> str`
- [ ] Build hidden marker line: `<!-- couplingguard:marker -->`
- [ ] Build hidden JSON data blob: `<!-- couplingguard:data:{"max_score": analysis.max_score, ...} -->`
- [ ] Build `<details>` summary line: `🔍 couplingguard — {N} pairs detected, highest risk: {emoji} {analysis.max_score:.2f}`
- [ ] If `analysis.previous_max_score is not None`: prepend delta line `> Score changed since last push: {prev_emoji} {prev:.2f} → {curr_emoji} {curr:.2f}`
- [ ] Build markdown table header: `| File in PR | Coupled With | Score | Risk | Co-changes |`
- [ ] Build table separator row
- [ ] Build each table row via `render_table_row(pair)` for pair in `analysis.pairs`
- [ ] If any pair has `suggested_owners`: append `**Suggested reviewers for coupled files:** {owners_str}`
- [ ] If `analysis.pairs` is empty: body is `_No coupling patterns detected in this PR's changed files._`
- [ ] Assemble full `<details>...</details>` block with marker and JSON blob prepended
- [ ] Return complete comment body string

### 9.4 Informational Comment (renderer.py)
- [ ] Define `def render_info_comment(reason: str) -> str`
- [ ] Return simple comment body: `<!-- couplingguard:marker --> ℹ️ couplingguard: {reason}`
- [ ] Used for: shallow clone error, too-few-commits warning, empty PR files

---

## Phase 10: GitHub Poster

### 10.1 GitHub Client Init (github_poster.py)
- [ ] Import `github`, `github.Auth`, `os`, `time`, `models.GitHubAuthError`
- [ ] Define `def get_github_client(token: str) -> github.Github`
- [ ] Instantiate `github.Github(auth=github.Auth.Token(token))`
- [ ] Return client

### 10.2 Find Existing Comment (github_poster.py)
- [ ] Define `MARKER = "<!-- couplingguard:marker -->"`
- [ ] Define `def find_existing_comment(pr) -> Optional[github.IssueComment.IssueComment]`
- [ ] Call `pr.get_issue_comments()` (paginated; iterate all pages)
- [ ] For each comment: if `MARKER in comment.body`, return comment
- [ ] Return `None` if not found

### 10.3 Post or Edit Comment (github_poster.py)
- [ ] Define `def post_comment(pr, body: str, dry_run: bool) -> None`
- [ ] If `dry_run`: print body to stdout and return
- [ ] Call `find_existing_comment(pr)`
- [ ] If existing: call `comment.edit(body)`
- [ ] If not existing: call `pr.create_issue_comment(body)`
- [ ] Wrap in try/except `github.GithubException`: if `status == 403`: raise `GitHubAuthError`

### 10.4 Rate Limit Handling (github_poster.py)
- [ ] Wrap `post_comment` call in retry logic
- [ ] Catch `github.RateLimitExceededException`
- [ ] Extract `reset_timestamp` from exception; call `time.sleep(reset_timestamp - time.time() + 5)`
- [ ] Retry once; if still fails, log ERROR and re-raise

### 10.5 Fail Threshold Check (github_poster.py)
- [ ] Define `THRESHOLD_SCORES = {"low": 0.3, "medium": 0.7, "high": 0.7}`

  _Correction:_ `{"low": 0.3, "medium": 0.3, "high": 0.7}` — "fail if score exceeds this level's min"
  
  _Actual mapping:_ fail_threshold=`"low"` means "fail if any pair is Low or above" (score >= 0.0), `"medium"` = score >= 0.3, `"high"` = score >= 0.7
  
- [ ] Define `FAIL_THRESHOLD_MINIMUMS = {"low": 0.0, "medium": 0.3, "high": 0.7}`
- [ ] Define `def check_fail_threshold(analysis: PRAnalysis, config: Config) -> bool`
- [ ] If `config.fail_threshold is None`: return `False`
- [ ] Get minimum from `FAIL_THRESHOLD_MINIMUMS[config.fail_threshold]`
- [ ] If `analysis.max_score >= minimum`: log failure message and return `True`
- [ ] Return `False`

### 10.6 Full GitHub Post Flow (github_poster.py)
- [ ] Define `def run_github_flow(analysis: PRAnalysis, comment_body: str, config: Config, token: str) -> int`
- [ ] Get client via `get_github_client(token)`
- [ ] Extract repo name from `os.environ["GITHUB_REPOSITORY"]` (`"owner/repo"`)
- [ ] Call `client.get_repo(repo_name)`
- [ ] Call `repo.get_pull(analysis.pr_number)`
- [ ] Call `post_comment(pr, comment_body, config.dry_run)`
- [ ] Call `check_fail_threshold(analysis, config)` → if `True`, return exit code `1`
- [ ] Return `0`

---

## Phase 11: GitLab Poster

### 11.1 GitLab Environment Detection (gitlab_poster.py)
- [ ] Import `os`, `gitlab`, `models.CouplingGuardError`
- [ ] Define `def is_gitlab_ci() -> bool`: check `os.environ.get("CI_SERVER_URL")` is not None
- [ ] Define `def get_mr_iid() -> int`: return `int(os.environ["CI_MERGE_REQUEST_IID"])`
- [ ] Define `def get_project_id() -> str`: return `os.environ["CI_PROJECT_ID"]`

### 11.2 GitLab Client Init (gitlab_poster.py)
- [ ] Define `def get_gitlab_client(token: str) -> gitlab.Gitlab`
- [ ] Instantiate `gitlab.Gitlab(os.environ["CI_SERVER_URL"], private_token=token)`
- [ ] Call `gl.auth()` to verify token; catch `gitlab.exceptions.GitlabAuthenticationError` and raise `CouplingGuardError`

### 11.3 Find Existing MR Note (gitlab_poster.py)
- [ ] Define `def find_existing_note(mr) -> Optional[object]`
- [ ] Call `mr.notes.list(all=True)` (python-gitlab auto-paginates with `all=True`)
- [ ] For each note: if `MARKER in note.body`, return note
- [ ] Return `None`

### 11.4 Post or Edit MR Note (gitlab_poster.py)
- [ ] Define `def post_mr_note(mr, body: str, dry_run: bool) -> None`
- [ ] If `dry_run`: print body and return
- [ ] Call `find_existing_note(mr)`
- [ ] If existing: call `note.body = body`, then `note.save()`
- [ ] If not existing: call `mr.notes.create({"body": body})`

### 11.5 Full GitLab Post Flow (gitlab_poster.py)
- [ ] Define `def run_gitlab_flow(analysis: PRAnalysis, comment_body: str, config: Config, token: str) -> int`
- [ ] Get client, get project via `gl.projects.get(get_project_id())`
- [ ] Get MR via `project.mergerequests.get(get_mr_iid())`
- [ ] Call `post_mr_note(mr, comment_body, config.dry_run)`
- [ ] Call `check_fail_threshold(analysis, config)` → if `True`, return `1`
- [ ] Return `0`

---

## Phase 12: Dashboard Writer

### 12.1 History JSON Management (dashboard.py)
- [ ] Import `json`, `datetime`, `pathlib.Path`, `models.PRAnalysis`
- [ ] Define `HISTORY_FILE = "coupling-history.json"`
- [ ] Define `def load_history(repo_root: Path) -> list[dict]`
- [ ] Check if `coupling-history.json` exists; if yes: `json.loads(path.read_text())`
- [ ] If file missing: return `[]`
- [ ] Catch `json.JSONDecodeError`: log WARNING and return `[]`

### 12.2 History Entry Append (dashboard.py)
- [ ] Define `def append_to_history(history: list[dict], analysis: PRAnalysis) -> list[dict]`
- [ ] Build entry: `{"date": datetime.now().isoformat()[:10], "pr": analysis.pr_number, "max_score": analysis.max_score, "risk": analysis.pr_risk, "pair_count": len(analysis.pairs)}`
- [ ] Append entry to history list
- [ ] Return updated list

### 12.3 History File Write (dashboard.py)
- [ ] Define `def save_history(history: list[dict], repo_root: Path) -> None`
- [ ] Write `json.dumps(history, indent=2)` to `coupling-history.json`

### 12.4 HTML Dashboard Generation (dashboard.py)
- [ ] Define `def generate_dashboard_html(history: list[dict]) -> str`
- [ ] Build HTML string template with embedded `<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>`
- [ ] Build Chart.js `Line` chart config: `labels` = date strings, `datasets[0].data` = `max_score` values per entry
- [ ] Color dataset line: green below 0.3, yellow 0.3–0.7, red above 0.7 (use single color `#f59e0b` for simplicity in v1)
- [ ] Include second dataset for `pair_count` on secondary y-axis
- [ ] Add `<table>` below chart showing last 20 entries: date, PR number, max score, risk emoji, pair count
- [ ] Return complete HTML string

### 12.5 Dashboard File Write (dashboard.py)
- [ ] Define `def save_dashboard(html: str, output_dir: Path) -> None`
- [ ] Write html to `output_dir / "coupling-dashboard.html"`

---

## Phase 13: Main Entry Point

### 13.1 CLI Entry Point (cli.py)
- [ ] Import `argparse`, `sys`, `pathlib.Path`, `logging`
- [ ] Define `def main() -> None`
- [ ] Set up `logging.basicConfig(level=logging.DEBUG if os.environ.get("COUPLINGGUARD_DEBUG") else logging.INFO)`
- [ ] Parse args: `--repo` (default: `.`), `--lookback-days`, `--dry-run`
- [ ] Call `run(repo_root=Path(args.repo), action_inputs=vars(args))`
- [ ] Exit with returned code via `sys.exit(code)`

### 13.2 Core Run Function (__init__.py)
- [ ] Import all modules
- [ ] Define `def run(repo_root: Path, action_inputs: dict) -> int`
- [ ] Load config: `config = load_config(repo_root, action_inputs)`
- [ ] Open repo: `repo = open_repo(repo_root)` — catch `ShallowCloneError` → post info comment, exit 1
- [ ] Parse git history: `commits = get_commits(repo, config.lookback_days)`
- [ ] If `len(commits) == 0`: post info comment "No commits in lookback window", exit 0
- [ ] Build matrix: `matrix = build_normalized_matrix(commits, config)`
- [ ] Load PR files: `pr_number, pr_files = load_pr_files()`
- [ ] If `not pr_files`: post info comment "No changed files detected", exit 0
- [ ] Analyze PR: `analysis = analyze_pr(pr_files, matrix, file_counts, config)`
- [ ] Load CODEOWNERS: `codeowners = load_codeowners(repo_root)`
- [ ] Suggest reviewers: `suggest_reviewers(analysis.pairs, codeowners, pr_files)`
- [ ] Find previous comment body (GitHub/GitLab): call appropriate `find_existing_comment`
- [ ] Extract delta: if previous body: `analysis.previous_max_score = get_previous_max_score(previous_body)`
- [ ] Render comment: `comment_body = render_comment(analysis, config)`
- [ ] Post comment: route to `run_github_flow` or `run_gitlab_flow` based on `is_gitlab_ci()`
- [ ] If `config.publish_dashboard`: load history, append, save JSON, generate HTML, save HTML
- [ ] Return exit code from post flow

---

## Phase 14: action.yml

### 14.1 Composite Action Definition
- [ ] Set `name: couplingguard`, `description: "Detect file coupling risk in PRs from git co-change history"`
- [ ] Add input `github_token`: required false, default `${{ github.token }}`
- [ ] Add input `gitlab_token`: required false, default `""`
- [ ] Add input `lookback_days`: required false, default `"90"`
- [ ] Add input `min_occurrences`: required false, default `"3"`
- [ ] Add input `max_pairs`: required false, default `"10"`
- [ ] Add input `low_threshold`: required false, default `"0.3"`
- [ ] Add input `high_threshold`: required false, default `"0.7"`
- [ ] Add input `fail_threshold`: required false, default `""`
- [ ] Add input `exclude`: required false, default `""`
- [ ] Add input `publish_dashboard`: required false, default `"false"`
- [ ] Add input `dry_run`: required false, default `"false"`
- [ ] Set `runs.using: composite`
- [ ] Add step: `uses: actions/setup-python@v5` with `python-version: "3.11"`
- [ ] Add step: `pip install couplingguard==${{ inputs.version || 'latest' }}` (or pin to action SHA)
- [ ] Add step: `run: couplingguard`, passing all inputs as `INPUT_*` env vars
- [ ] Add step: if `publish_dashboard == 'true'`: `uses: actions/upload-artifact@v4` with `coupling-dashboard.html`

### 14.2 Environment Variable Passing
- [ ] For each action input: set `env: INPUT_LOOKBACK_DAYS: ${{ inputs.lookback_days }}` in the run step
- [ ] Pass `GITHUB_TOKEN: ${{ inputs.github_token }}`
- [ ] Pass `GITLAB_TOKEN: ${{ inputs.gitlab_token }}`

---

## Phase 15: README Badge

### 15.1 Shields.io Endpoint Badge
- [ ] After first successful run: commit `coupling-score.json` to repo root with format `{"schemaVersion": 1, "label": "coupling", "message": "🟢 low", "color": "brightgreen"}`
- [ ] Update `coupling-score.json` in `dashboard.py` after each run: set `message` based on `pr_risk`
- [ ] Add badge URL to README: `![coupling](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/OWNER/REPO/main/coupling-score.json)`
- [ ] Add `coupling-score.json` to `.gitignore` exclusion list (it should NOT be ignored — remove from gitignore)
- [ ] If `publish_dashboard: true`: add step to commit `coupling-score.json` to repo main branch via `github_token`

---

## Phase 16: Unit Tests

### 16.1 Test Fixtures (conftest.py)
- [ ] Define `@pytest.fixture fake_repo(tmp_path)`: call `git.Repo.init(tmp_path)`, configure user email and name via `repo.config_writer()`
- [ ] In `fake_repo`: add helper method `commit(files: list[str])` that creates empty files, stages all, and commits with message `"test commit"`
- [ ] Define `@pytest.fixture fake_pr_event(tmp_path)`: write JSON to temp file with `pull_request.number = 1` and `pull_request.changed_files = []`, set `GITHUB_EVENT_PATH` env var
- [ ] Define `@pytest.fixture mock_github`: return `MagicMock()` configured to simulate PyGithub `Github`, `Repo`, `PullRequest`, `IssueComment`

### 16.2 Git Parser Tests (test_git_parser.py)
- [ ] Test: shallow repo raises `ShallowCloneError`
- [ ] Test: commits older than `lookback_days` not included
- [ ] Test: merge commits excluded (commit with multiple parents)
- [ ] Test: `.png` file excluded from file list
- [ ] Test: files matching exclude glob `"docs/**"` excluded
- [ ] Test: empty commit list returned when no commits in window

### 16.3 Matrix Tests (test_matrix.py)
- [ ] Test: two files in same commit → `co_change[a][b] == 1`
- [ ] Test: two files in 5 commits → `co_change[a][b] == 5`
- [ ] Test: normalization: co=10, count_a=10, count_b=20 → `score = 10/20 = 0.5`
- [ ] Test: pair with `co_change < min_occurrences` not in output
- [ ] Test: pair with `co_change >= min_occurrences` in output
- [ ] Test: empty commits input → empty matrix returned

### 16.4 PR Analyzer Tests (test_pr_analyzer.py)
- [ ] Test: only pairs involving `pr_files` returned
- [ ] Test: pairs sorted by score descending
- [ ] Test: `max_pairs=2` truncates to 2 pairs even if 5 available
- [ ] Test: score `0.29` → risk `"low"`
- [ ] Test: score `0.30` → risk `"medium"`
- [ ] Test: score `0.699` → risk `"medium"`
- [ ] Test: score `0.70` → risk `"high"`
- [ ] Test: empty PR files → empty `PRAnalysis.pairs`

### 16.5 Config Tests (test_config.py)
- [ ] Test: valid YAML file loaded, `lookback_days` set correctly
- [ ] Test: action input `lookback_days = "180"` overrides YAML `lookback_days: 90`
- [ ] Test: missing YAML file → `Config()` with all defaults
- [ ] Test: invalid YAML file → `ConfigError` raised with message containing line number
- [ ] Test: `fail_threshold` value `"high"` loaded correctly
- [ ] Test: multiline `exclude` input split correctly into list

### 16.6 Renderer Tests (test_renderer.py)
- [ ] Test: `<!-- couplingguard:marker -->` present in output
- [ ] Test: `<!-- couplingguard:data:` present in output with valid JSON
- [ ] Test: `max_score` in hidden JSON matches `analysis.max_score`
- [ ] Test: `<details>` and `</details>` tags present
- [ ] Test: table has header row `| File in PR | Coupled With | Score | Risk | Co-changes |`
- [ ] Test: correct number of table rows equal `len(analysis.pairs)`
- [ ] Test: delta line appears when `previous_max_score` set
- [ ] Test: delta line absent when `previous_max_score` is `None`
- [ ] Test: `🟢` emoji appears for low-risk pair
- [ ] Test: suggested reviewers line appears when `suggested_owners` non-empty
- [ ] Test: empty pairs → "No coupling patterns detected" message

### 16.7 Delta Tests (test_delta.py)
- [ ] Test: valid JSON blob extracted → returns dict with `max_score`
- [ ] Test: malformed JSON → returns `None`, no exception raised
- [ ] Test: no marker in comment body → returns `None`
- [ ] Test: marker present but empty JSON object → returns empty dict

### 16.8 CODEOWNERS Tests (test_codeowners_loader.py)
- [ ] Test: `@username` owner returned for matched path
- [ ] Test: `user@example.com` email owner returned for matched path
- [ ] Test: no CODEOWNERS file → `load_codeowners` returns `None`
- [ ] Test: `suggest_reviewers` returns empty list when `codeowners is None`

### 16.9 Dashboard Tests (test_dashboard.py)
- [ ] Test: new history file created with one entry when none exists
- [ ] Test: existing history file has entry appended (2 entries after 2 runs)
- [ ] Test: generated HTML contains `chart.js` CDN script tag
- [ ] Test: generated HTML contains `coupling-dashboard` in title
- [ ] Test: `coupling-score.json` written with correct `message` for "high" risk

---

## Phase 17: Integration Tests

### 17.1 GitHub Poster Integration (test_github_poster.py)
- [ ] Test: first run → `pr.create_issue_comment()` called once with body containing marker
- [ ] Test: second run with existing comment → `comment.edit()` called, `create_issue_comment` NOT called
- [ ] Test: `dry_run=True` → neither `create_issue_comment` nor `comment.edit()` called; body printed to stdout
- [ ] Test: `fail_threshold="high"` with `max_score=0.82` → `run_github_flow` returns `1`
- [ ] Test: `fail_threshold="high"` with `max_score=0.60` → `run_github_flow` returns `0`
- [ ] Test: `fail_threshold=None` with `max_score=0.99` → returns `0`
- [ ] Test: `RateLimitExceededException` → sleep called, retry attempted
- [ ] Test: `GithubException(403)` → `GitHubAuthError` raised

### 17.2 GitLab Poster Integration (test_gitlab_poster.py)
- [ ] Test: first run → `mr.notes.create()` called with body containing marker
- [ ] Test: second run with existing note → `note.save()` called, `notes.create()` NOT called
- [ ] Test: `dry_run=True` → `notes.create()` not called; body printed
- [ ] Test: `GitlabAuthenticationError` → `CouplingGuardError` raised

---

## Phase 18: E2E Tests

### 18.1 Full Workflow E2E (test_e2e.py)
- [ ] Test: init repo with 10 scripted commits (files A, B co-change 8 times) → run couplingguard → verify `CouplingPair(file_a, file_b, score=0.8)` in result
- [ ] Test: PR with 0 changed files → `PRAnalysis.pairs == []`, exit code 0
- [ ] Test: repo with 2 commits total, `min_occurrences=3` → empty pairs, informational comment rendered

---

## Phase 19: Documentation

### 19.1 README
- [ ] Add shields.io badge: `![coupling](https://img.shields.io/endpoint?url=...)` at top
- [ ] Add CI badge for main branch
- [ ] Add "Install in 5 lines" section with minimal YAML snippet
- [ ] Add "Inputs" table with all 12 inputs, types, defaults, descriptions
- [ ] Add "PR Comment Example" section with screenshot (or ASCII art of comment)
- [ ] Add "How it works" section: git log → co-change matrix → normalization → PR filter → comment
- [ ] Add "Local CLI usage" section: `pip install couplingguard && couplingguard --repo .`
- [ ] Add "GitLab CI" section with YAML snippet using `GITLAB_TOKEN`
- [ ] Add "Permissions" section explaining `pull-requests: write` requirement
- [ ] Add "FAQ" section: "Why fetch-depth: 0?", "What is normalization?", "Does this work on monorepos?"

### 19.2 GitHub Marketplace Listing
- [ ] Set `branding.icon: "git-branch"` and `branding.color: "orange"` in `action.yml`
- [ ] Write Marketplace description (< 125 characters): "Detect file coupling risk in PRs using git co-change history. Zero-config, no external services."
- [ ] Tag with: `code-quality`, `pull-request`, `git`, `coupling`, `static-analysis`
