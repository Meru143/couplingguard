# Launch tweet thread

Pre-written thread for X / Bluesky / LinkedIn (lightly adapt per network).
Each tweet sticks to ~270 chars. Pin tweet 1.

---

**1/8 — Hook**

Two files that always break together still ship in the same PR with no one
looking at both sides.

`couplingguard` is a free GitHub Action that calls this out at PR time —
before the bug, not after the post-mortem.

→ github.com/Meru143/couplingguard

---

**2/8 — The pain**

Your repo already knows which files are coupled. Every co-change in the git
log is a hint:

  src/payment.py + src/billing.py → 41 times
  src/payment.py + tests/test_billing.py → 32 times

That signal has been sitting in `git log` the whole time. No one looks at it.

---

**3/8 — What it does**

On every PR, couplingguard posts a comment with the top coupled pairs
involving your PR's changed files:

  | File in PR | Coupled with | Score | Risk |
  | payment.py | billing.py   | 0.82  | 🔴   |
  | payment.py | test_bill.py | 0.64  | 🟡   |

🟢 < 0.3 ≤ 🟡 < 0.7 ≤ 🔴

---

**4/8 — Normalization is the trick**

Raw "they changed together 5 times" is noise. Normalized is signal:

  score = co_changes / max(file_a_total, file_b_total)

Pair changed 5 times, file_a changed 100 times → score 0.05 (noise).
Pair changed 5 times, both changed 5 times → score 1.00 (always coupled).

No existing free tool does this.

---

**5/8 — Why this matters now**

AI coding agents land PRs touching 20+ files at once. Coupling risk has
never been higher and review surface has never been wider.

A comment that says "these two always break together — actually look at
both" is the cheapest bug-prevention tool in your stack.

---

**6/8 — Install**

5 lines of YAML, no signup, no hosted service:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
- uses: Meru143/couplingguard@v1
```

GitLab CI works the same way with a `GITLAB_TOKEN`.

---

**7/8 — What you get on top**

• Delta line on re-push: `🟡 0.45 → 🔴 0.82`
• CODEOWNERS-aware reviewer suggestions for coupled files
• Optional `fail_threshold: high` to enforce a coupling budget in CI
• Static dashboard + shields.io badge for trend tracking

---

**8/8 — Compared to alternatives**

vs CodeScene → free + OSS + no external service
vs code-maat → 2016 Clojure CLI, no PR comments, no normalization
vs Danger.js → you write the rules; couplingguard ships them
vs CODEOWNERS → static ownership; couplingguard adds dynamic co-change

MIT licensed. Try it: github.com/Meru143/couplingguard
