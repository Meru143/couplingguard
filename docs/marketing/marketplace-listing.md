# GitHub Marketplace listing copy

GitHub Marketplace lets you set:
- **Title** (the action's name, fixed to `couplingguard`)
- **Tagline** (≤ 125 chars — pulled from `description:` in action.yml)
- **Description** (markdown, full body of the listing page)
- **Categories** (pick 2)
- **Featured tags** (5 short keywords)

## Tagline (≤ 125 chars)

**Current** (in `action.yml`, 96 chars):

> Detect file coupling risk in PRs using git co-change history. Zero-config, no external services.

This is good. Don't change unless you also update `action.yml`.

## Categories (pick 2 from GitHub's fixed list)

1. **Code quality**
2. **Continuous integration**

## Featured tags

`code-quality`, `pull-request`, `git`, `coupling`, `static-analysis`

## Long description (paste into the Marketplace listing page)

```markdown
**couplingguard** posts a collapsible comment on every PR showing which
files in your repo's history co-change with the files your PR touches.
It surfaces hidden coupling at the moment it matters most: code review,
before merge.

## What you'll see on every PR

A markdown comment like this, automatically:

| File in PR | Coupled with | Score | Risk | Co-changes |
|------------|--------------|-------|------|------------|
| `src/payment.py` | `src/billing.py` | 0.82 | 🔴 High | 41/50 commits |
| `src/payment.py` | `tests/test_billing.py` | 0.64 | 🟡 Medium | 32/50 commits |

> **Suggested reviewers for coupled files:** @alice, @team-payments

On re-push, the comment edits itself with a delta line:

> ⚠️ Score changed since last push: 🟡 0.45 → 🔴 0.82 ↑

## How the score works

`score = co_changes / max(file_a_total_changes, file_b_total_changes)`

This produces a 0–1 ratio that's comparable across repos of any size and
age. Pair changed together 5 times when file_a changed 100 times overall?
Score 0.05 — noise. Pair changed together 5 times when both files only
changed 5 times each? Score 1.00 — they're always coupled.

## Why use it

- **AI coding agents land big PRs.** 20-30 files touched at once is now
  normal. Coupling risk has never been higher or harder to see by
  scrolling a diff.
- **No existing free tool does this.** code-maat is post-hoc, CodeScene
  is $1k+/month, CODEOWNERS only knows static ownership.
- **Zero signup, no hosted service.** Composite Action runs in your CI.
  All data stays in your repo.

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
          fetch-depth: 0          # full git log required
      - uses: Meru143/couplingguard@v1
        with:
          github_token: ${{ github.token }}
```

## Optional CI gate

Set `fail_threshold: high` to fail the build when any pair in the PR
crosses 0.7. Teams use this to enforce a coupling budget — coupling
entropy doesn't compound silently for months.

## GitLab CI supported

Same algorithm, posts an MR note via python-gitlab. Set `GITLAB_TOKEN`
in your project's CI/CD variables.

## License

MIT. Source on [GitHub](https://github.com/Meru143/couplingguard).
```
