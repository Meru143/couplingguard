# Marketing assets

Ready-to-use copy and assets for launching, marketing, and growing couplingguard.

| File | What it is | When to use |
|---|---|---|
| [`launch-checklist.md`](launch-checklist.md) | Hour-by-hour launch playbook (T-24h → T+30d) | Day before / day of launch |
| [`launch-tweet-thread.md`](launch-tweet-thread.md) | 8-tweet pre-written thread for X / Bluesky / LinkedIn | Launch day |
| [`show-hn-post.md`](show-hn-post.md) | Show HN title + body draft | Launch day morning |
| [`blog-post.md`](blog-post.md) | 1000-word blog post draft | Cross-post to dev.to / Hashnode / personal blog |
| [`marketplace-listing.md`](marketplace-listing.md) | GitHub Marketplace listing copy + category + featured tag choices | When you click "Publish this Action to the Marketplace" |
| [`coupling-cheatsheet.md`](coupling-cheatsheet.md) | 1-page reference PDF (formula, thresholds, common couplings, tuning guide) | Lead magnet for newsletter / docs site / X bio link |

## Visual assets (in `assets/` at repo root)

- `hero-banner.svg` — 1200x320 banner for README top, social preview, slide decks
- `animated-demo.svg` — 1200x600 self-contained animated walkthrough of the data flow + rendered PR comment (renders inline in GitHub README)

## Video assets (in `demo/remotion/` at repo root)

Optional Remotion project for rendering a real MP4 / GIF demo:

```bash
cd demo/remotion
npm install
npm start         # opens Remotion Studio in browser
npm run build     # renders out/couplingguard-demo.mp4
```

See `demo/remotion/README.md` for the full workflow.

## Voice & tone

These materials follow a few rules consistent with the README:

- **Specific over vague** — "5 lines of YAML" not "easy install"; "0.82 score" not "high coupling"
- **Benefits over features** — "the cheapest bug-prevention tool in your stack" not "co-change analysis with normalized scoring"
- **Honest over sensational** — no fabricated stats, no fake testimonials
- **Active voice** — "couplingguard posts" not "comments are posted"
- **Confident, not qualified** — "always" / "every" rather than "may" / "should" when accurate

Adapt voice for your channel — LinkedIn skews more professional, X/HN
skews more direct, blog post skews more narrative — but keep the
substance and the specifics intact.
