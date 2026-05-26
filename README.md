# couplingguard

[![coupling](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Meru143/couplingguard/main/coupling-score.json)](https://github.com/Meru143/couplingguard)
[![CI](https://github.com/Meru143/couplingguard/actions/workflows/ci.yml/badge.svg)](https://github.com/Meru143/couplingguard/actions/workflows/ci.yml)

Detect file coupling risk in pull requests from git co-change history. A free GitHub Action that posts a collapsible HTML comment on every PR with normalized coupling scores for the changed files, suggests reviewers from CODEOWNERS for the coupled files, edits itself with a delta line on re-push, and can optionally fail the build above a configurable threshold.

GitLab CI is supported via the same algorithm — set `GITLAB_TOKEN` and the action posts an MR note instead.

## Install in 5 lines

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
          fetch-depth: 0     # required: couplingguard needs the full git log
      - uses: Meru143/couplingguard@v1
        with:
          github_token: ${{ github.token }}
```

## What the PR comment looks like

```
🔍 couplingguard — 2 pairs detected, highest risk: 🔴 0.82

> ⚠️ Score changed since last push: 🟡 0.45 → 🔴 0.82 ↑

| File in PR        | Coupled With            | Score | Risk      | Co-changes      |
|-------------------|-------------------------|-------|-----------|-----------------|
| `src/payment.py`  | `src/billing.py`        | 0.82  | 🔴 High   | 41/50 commits   |
| `src/payment.py`  | `tests/test_billing.py` | 0.64  | 🟡 Medium | 32/50 commits   |

Suggested reviewers for coupled files: @alice, @team-payments
```

The comment is collapsible (`<details>`-wrapped) and edits itself on every push to the PR with a "score changed" line showing the delta.

## Inputs

| Input | Type | Default | Description |
|---|---|---|---|
| `github_token` | string | `${{ github.token }}` | Token for PR comment + check |
| `gitlab_token` | string | `""` | Personal access token for GitLab CI |
| `lookback_days` | number | `90` | Days of history to analyze |
| `min_occurrences` | number | `3` | Minimum co-change count to include a pair |
| `max_pairs` | number | `10` | Maximum pairs shown in the comment |
| `low_threshold` | number | `0.3` | Score boundary 🟢 → 🟡 |
| `high_threshold` | number | `0.7` | Score boundary 🟡 → 🔴 |
| `fail_threshold` | string | `""` | `low`/`medium`/`high` to fail CI; empty disables |
| `exclude` | string | `""` | Newline-separated glob patterns |
| `publish_dashboard` | boolean | `false` | Generate static dashboard + history + badge artifact |
| `dry_run` | boolean | `false` | Print comment to stdout; don't post |

## How it works

```
git log (lookback_days, no-merges)
   │
   ▼
co-change matrix  (file pairs x commit count)
   │
   ▼
normalize         (score = co_count / max(file_a_commits, file_b_commits))
   │
   ▼
PR filter         (only pairs where one side is in PR.changed_files)
   │
   ▼
classify          (🟢 < 0.3 ≤ 🟡 < 0.7 ≤ 🔴)
   │
   ▼
render + post
```

The key insight is normalization: raw co-change counts inflate for old/big files, while `co / max(count)` produces a 0–1 ratio that's comparable across repos of any size and age.

## Local CLI

```bash
pip install couplingguard
couplingguard --repo . --dry-run --lookback-days 90
```

The CLI uses the same code as the Action; `--dry-run` prints the rendered comment to stdout without trying to reach GitHub.

## GitLab CI

```yaml
coupling:
  image: python:3.11
  script:
    - pip install couplingguard
    - couplingguard --repo .
  variables:
    GITLAB_TOKEN: ${GITLAB_TOKEN}
  only:
    - merge_requests
```

`CI_SERVER_URL`, `CI_PROJECT_ID`, and `CI_MERGE_REQUEST_IID` are auto-set by every GitLab Runner.

## Permissions

couplingguard needs:
- `contents: read` to read the git history.
- `pull-requests: write` to post / edit the comment.

That's it. Nothing else is touched.

## FAQ

**Why `fetch-depth: 0`?** Default `actions/checkout@v4` does a shallow clone (depth=1). couplingguard needs the full log to count co-changes. If you forget, the action exits 1 with an actionable error rather than producing wrong results.

**What is normalization?** A pair where `a.py` was touched 100 times, `b.py` 5 times, and both together 5 times is *not* the same as a pair where both were touched 5 times each. Raw count = 5 in both cases. Normalized: 5/100 = 0.05 vs 5/5 = 1.00. The second pair is genuinely coupled; the first is noise.

**Does this work on monorepos?** Yes. Use `exclude` to drop noisy paths (docs, migrations) and bump `min_occurrences` to filter rare pairs. The matrix is built once per run and scales linearly with `lookback_days × avg_files_per_commit`.

**What if my repo has fewer than `min_occurrences` commits?** The action posts an informational comment and exits 0 — no false failures on new repos.

## Differentiators

- **vs CodeScene** — Free, OSS, runs entirely in your CI. CodeScene is $1k+/month.
- **vs code-maat** — 2016 Java toy, unmaintained, no Action, no normalization. couplingguard is a maintained Python Action with PR-time comments.
- **vs Danger.js** — Danger requires you to write coupling rules yourself. couplingguard ships them.
- **vs CODEOWNERS** — Static ownership vs dynamic co-change. Complementary: couplingguard uses CODEOWNERS to suggest *better* reviewers.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bugs → [Issues](https://github.com/Meru143/couplingguard/issues). Security → [SECURITY.md](SECURITY.md).

## Publishing to the GitHub Marketplace

GitHub Marketplace categories and featured tags are configured **in the
GitHub web UI**, not in `action.yml`. After tagging a release:

1. Open the new release on the **Releases** page.
2. Click **Publish this Action to the GitHub Marketplace**.
3. Accept the Marketplace terms.
4. Choose **two categories** from the dropdown — recommended:
   *Code quality* and *Continuous integration*.
5. Add **featured tags**: `code-quality`, `pull-request`, `git`,
   `coupling`, `static-analysis`.

The `branding.icon` (`git-branch`) and `branding.color` (`orange`) from
`action.yml` are picked up automatically as the listing badge.

## License

MIT. See [LICENSE](LICENSE).
