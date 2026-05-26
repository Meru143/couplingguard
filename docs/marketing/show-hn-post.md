# Show HN draft

## Title (≤ 80 chars)

`Show HN: Couplingguard – Free GitHub Action that flags file coupling in PRs`

Alternates if the first doesn't feel right:
- `Show HN: I built a free coupling-risk PR-comment Action for git repos`
- `Show HN: Couplingguard – co-change analysis for pull requests, in 5 lines of YAML`

## Body (HN tolerates 200-400 words for Show HN)

Hi HN — I made couplingguard, a free GitHub Action that analyzes your
repo's git history at PR open time and posts a comment showing which files
historically co-changed with the files in the PR. Score per pair is
normalized (co_changes / max(file_a_total, file_b_total)) so it's
comparable across repos of any size.

What it actually outputs on a PR:

  | File in PR       | Coupled with             | Score | Risk |
  | src/payment.py   | src/billing.py           | 0.82  | 🔴   |
  | src/payment.py   | tests/test_billing.py    | 0.64  | 🟡   |

The motivation: AI coding agents (Copilot, Claude Code, Cursor) routinely
land PRs touching 15-30 files at once. Reviewers can't hold the whole
diff in their head, and traditional CODEOWNERS only knows static
ownership — not which files have historically broken together when
modified in the same commit. couplingguard surfaces the dynamic
co-change signal so a reviewer reading one file sees "these others
almost always change with it — actually look at both."

Why I think this is interesting:

1. **The signal has always been there.** Every co-change in `git log` is a
   coupling hint. No free tool extracts it into PR comments. CodeScene
   does this but costs $1k+/month and runs as a hosted service.

2. **Normalization matters.** Raw co-change counts are noisy. The
   normalized ratio is the actual signal — small files that always
   change together score 1.0; big "touched by everyone" files score
   near 0.

3. **It composes with CODEOWNERS.** When the PR touches `payment.py`
   and the coupled `billing.py` has a different owner not on the PR,
   couplingguard surfaces them as a suggested reviewer.

4. **Optional CI gate.** `fail_threshold: high` exits 1 when a PR's
   max coupling crosses the threshold — opt-in coupling budget without
   forcing it on anyone.

The whole thing is a Python composite Action — 158 tests, 86% coverage,
ruff + mypy strict. MIT, no hosted service. GitLab CI is supported the
same way. There's a `--dry-run` mode that prints the comment to stdout
so you can preview locally without touching GitHub.

Repo: https://github.com/Meru143/couplingguard

Things I'd love feedback on:

- Whether the `co_changes / max(count)` formula is the right
  normalization vs alternatives like Jaccard, lift, or PMI
- Whether the 🟢/🟡/🟡 thresholds at 0.3/0.7 feel right on real repos
- Anything obvious I'm missing for monorepo performance (the matrix
  pass is O(commits × avg_files_per_commit²) which is fine up to ~50k
  commits in the window, but I'd like to push higher)
