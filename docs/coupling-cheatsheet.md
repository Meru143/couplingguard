# Coupling Cheatsheet (1-page reference)

Use this as a free PDF lead magnet for the project newsletter / docs
site / X bio link. Convert to PDF with any markdown-to-PDF tool
(`pandoc`, `md-to-pdf`, the Marked.app workflow). Print-friendly at A4
/ US Letter.

---

## The one formula

```
score = co_changes / max(file_a_total_changes, file_b_total_changes)
```

`co_changes` = commits where both files appeared together.
`file_a_total_changes` = commits where file_a appeared at all.

Score is 0–1. Higher = more historically coupled.

---

## Risk thresholds

| Score range | Emoji | Meaning |
|---|---|---|
| `< 0.30` | 🟢 Low | Occasional co-change. Likely noise. |
| `≥ 0.30 < 0.70` | 🟡 Medium | Consistent pattern. Worth a glance. |
| `≥ 0.70` | 🔴 High | Almost always change together. Review both. |

Tunable per repo via `low_threshold` and `high_threshold` in
`action.yml` inputs or `.couplingguard.yml`.

---

## Common couplings to look for

| Pattern | Why it shows up | What to do |
|---|---|---|
| `src/foo.py ↔ tests/test_foo.py` | Test ships with code | Healthy. Don't fight it. |
| `src/foo.py ↔ src/bar.py` (different concerns) | Hidden dependency | Fix the design. |
| `src/foo.py ↔ src/foo_v2.py` | Migration left files in sync | Either delete the old one or finish the migration. |
| `.gitignore` ↔ everything | Touched in every config refactor | Add `.gitignore` to `exclude:` |
| `package.json` ↔ `pnpm-lock.yaml` | Always co-change by design | Add the lockfile to `exclude:` |
| `OpenAPI spec ↔ client code` | Generated code paired with spec | Either: keep coupled (intentional) or generate at build time |

---

## Tuning by repo type

| Repo type | `lookback_days` | `min_occurrences` | Notes |
|---|---|---|---|
| Solo / hobby | 365 | 2 | Short history needs longer window + lower min. |
| Small team product | 90 | 3 | Default. Most common case. |
| Monorepo (50+ devs) | 60 | 5 | Recent enough to be relevant; min raised to filter chatter. |
| Mature OSS library | 180 | 4 | Stable code, slow churn — wider window. |

Set in `.couplingguard.yml`:

```yaml
lookback_days: 60
min_occurrences: 5
exclude:
  - "package-lock.json"
  - "pnpm-lock.yaml"
  - "yarn.lock"
  - "docs/**"
  - "*.md"
```

---

## Reading a score

`0.82` means: of all commits where either file changed, 82% of them
touched both. The remaining 18% are commits that touched only one.

`1.00` is the maximum: every change to either file also changes the other.

This is **NOT a probability that the PR will break.** It's a historical
ratio. The interpretation is: *"in the past, when one of these files
changed, the other almost always changed too — so if you only changed
one this time, double-check."*

---

## When to enable `fail_threshold`

| State of repo | Recommendation |
|---|---|
| Just installed couplingguard | Leave unset. Get used to seeing the scores first. |
| 2-4 weeks of comments, scores feel calibrated | `fail_threshold: high` — fail on any 🔴 in the PR. |
| Mature, low-coupling codebase | `fail_threshold: medium` — fail on any 🟡 too. |
| Legacy codebase, can't refactor everything | `fail_threshold: high` + `exclude:` the known legacy paths |

You can always set it temporarily for a single PR via workflow input
override.

---

## What couplingguard does NOT do

- ❌ Predict bugs. It's a historical signal, not a model.
- ❌ Replace CODEOWNERS. It complements them.
- ❌ Modify your code. Read-only on the working tree.
- ❌ Send your code anywhere. All analysis is local to your runner.
- ❌ Handle Bitbucket or Azure DevOps (in v0.1.0).

---

## Install

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
- uses: Meru143/couplingguard@v1
  with:
    github_token: ${{ github.token }}
```

5 lines. MIT licensed. github.com/Meru143/couplingguard
