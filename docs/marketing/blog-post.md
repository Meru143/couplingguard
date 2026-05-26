# Blog post draft: *Your git log knows which files break together. Nobody's reading it.*

Target outlets (pick one):
- Personal blog → cross-post to dev.to, Hashnode, Substack
- HN Show post (different format — see `show-hn-post.md`)
- Tech newsletter (e.g. Console.dev, Pointer.io) as a featured tool

Target length: 900–1100 words. Below is a finished draft you can publish
as-is or trim.

---

## Your git log knows which files break together. Nobody's reading it.

Open any mature codebase and watch a senior engineer review a PR. They'll
scroll for thirty seconds, mutter "wait, did they update the billing tests
too?", check, find that no — they didn't — and leave a comment.

Six months later, someone else opens an identical PR. The senior engineer
isn't on the review this time. The PR ships. Billing breaks in production
the next day.

The pattern is older than code review itself: **two files that always
need to change together, where everyone with the institutional memory is
on PTO that week.** And the most frustrating part is that the signal is
sitting right there in your git log. Every commit that touched both
`payment.py` and `billing.py` is a data point. Hundreds of them. You
have a perfect map of which files in your codebase are coupled — and
nobody reads it.

### The normalization problem

You can't just count co-changes. Some files are touched in literally
every commit: `package.json`, `README.md`, `.gitignore`, the lockfile.
Raw co-change count makes them look maximally coupled to everything,
which is useless.

The fix is normalization:

```
score = co_changes / max(file_a_total_changes, file_b_total_changes)
```

A pair that changed together 5 times when file_a was touched 100 times
overall scores 0.05 — noise. A pair that changed together 5 times when
both files were only touched 5 times each scores 1.00 — they're always
coupled. The ratio is comparable across repos of any size, age, or
language.

This is the same insight Adam Tornhill wrote about in *Your Code as a
Crime Scene* and shipped in his tool [code-maat](https://github.com/adamtornhill/code-maat).
The catch with code-maat is that it's a 2016 Clojure CLI — you run it
against a checked-out repo, parse the CSV, stare at the spreadsheet. By
the time you've decided "these two files are coupled," the PR is merged
and you're writing the post-mortem.

The leverage point isn't post-hoc analysis. It's at PR open time, when
the reviewer is *already looking at* `payment.py` and a comment can say
"by the way, here are the four files that have historically broken when
this one changes." Two seconds of attention now, prevented incident
later.

### Why this is happening more, not less

Two trends collide.

First, **AI coding agents land bigger PRs**. Copilot, Claude Code,
Cursor, all the rest — they routinely produce diffs touching 15-30 files
at once. A human writes the PR description, but no human held the whole
change in their head as a unified mental model. Coupling risk has never
been higher or harder to spot.

Second, **CODEOWNERS doesn't help**. It encodes static ownership: who
should review which files. It has no concept of which files break
together when they change in the same commit. A PR touching only
`payment.py` doesn't trigger any reviewer beyond payment's owner — even
though `billing.py` has a 0.82 historical coupling with it and the
billing team would catch the bug instantly.

### What I built

[couplingguard](https://github.com/Meru143/couplingguard) is a free
GitHub Action (and Python CLI, and GitLab CI integration) that:

1. Walks 90 days of git log on PR open
2. Builds the symmetric co-change matrix
3. Normalizes scores against per-file commit totals
4. Filters to pairs involving the PR's changed files
5. Classifies each pair as 🟢 / 🟡 / 🔴 against configurable thresholds
6. Posts a collapsible markdown comment on the PR
7. Suggests reviewers from CODEOWNERS for the coupled files
8. Optionally fails the CI check above a configurable threshold
9. Edits the comment in place on re-push with a `🟡 0.45 → 🔴 0.82`
   delta line

Five lines of YAML to install:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
- uses: Meru143/couplingguard@v1
  with:
    github_token: ${{ github.token }}
```

No signup, no hosted service, MIT licensed. All your repo data stays in
your repo. The Action runs entirely on your runner, posts via the
GitHub API, and produces an artifact-uploadable static trend dashboard
if you set `publish_dashboard: true`.

### Why this is the cheapest bug-prevention tool in your stack

Not because the algorithm is fancy. The algorithm is undergraduate
statistics. It's cheap because:

- **The signal is already in your repo** — no data to collect, no
  infrastructure to run, no events to instrument.
- **The intervention happens at PR time** — when attention is highest and
  fixes are cheapest.
- **It composes with CODEOWNERS** — you get *better* reviewer
  suggestions for free, on top of static ownership.
- **It's opt-in to fail CI** — start with informational comments only,
  add a fail threshold once you trust the numbers.

### Try it

Install on your repo, watch one real PR get reviewed. The first time you
see the comment surface a pair you hadn't thought about — that's the
moment.

Repo + install instructions: [github.com/Meru143/couplingguard](https://github.com/Meru143/couplingguard)

If you ship coupling-risk regressions in spite of CODEOWNERS, this is
free, takes 90 seconds to install, and starts producing PR comments
on the next PR you open.
