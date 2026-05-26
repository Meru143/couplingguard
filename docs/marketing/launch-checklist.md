# Launch day checklist

A focused playbook for the day couplingguard goes public. Each item has
a time estimate and a "skip if" condition so you can adapt to your
energy / bandwidth.

## T-24h (the day before)

- [ ] **Smoke test the whole flow end-to-end.** Open a real PR against
      a fork of couplingguard itself, confirm the action posts a real
      comment. (5 min)
- [ ] **Make repo public.** Settings → Visibility → Public.
      Marketplace requires it. (1 min)
- [ ] **Verify the badge URL renders** in the live README on
      github.com/Meru143/couplingguard. (1 min)
- [ ] **Pre-write your tweet thread + Show HN post.** Use
      `launch-tweet-thread.md` and `show-hn-post.md` as starting points.
      Tweak voice. (15 min)
- [ ] **Take a real screenshot of the PR comment** rendered on a real
      PR. Save as `assets/screenshot-pr-comment.png`. Update README's
      "What the PR comment looks like" section to use it instead of the
      markdown table. (10 min)
- [ ] **Sleep well.** Posting Show HN on three hours of sleep is a bad
      idea — you'll need bandwidth to answer comments for ~6 hours
      after submission.

## Launch day

### Morning (publish window: 7-9 AM your local time, or 9 AM ET / 6 AM PT for US visibility)

- [ ] **Submit to Hacker News** as a Show HN. (Title + post body from
      `show-hn-post.md`.) The first 60 minutes matter — be at the
      keyboard to answer comments.
- [ ] **Tweet the thread** (`launch-tweet-thread.md`). Tag relevant
      people if you've already had conversations with them; otherwise
      don't spam. Pin tweet 1.
- [ ] **Post to LinkedIn** with a shorter version focused on the
      "AI agents land big PRs" angle — LinkedIn responds well to that
      framing.
- [ ] **Post to r/programming** (link only, with a comment explaining
      what it is) and **r/devops** (text post). r/Python is also a fit.
      Skip if you don't have an established account on those subs —
      throwaway accounts get auto-flagged.

### Midday

- [ ] **Reply to every HN / Twitter comment within 30 min of receiving
      it** for the first 6 hours. Engagement velocity is what drives
      ranking.
- [ ] **DM 5-10 people you know personally** who work in platform
      engineering / devtools. Don't ask for upvotes — ask "would this
      be useful to your team?" and listen.
- [ ] **Add a GitHub release note** at v0.1.0 quoting one or two of
      the best HN comments (after a few hours). It signals momentum to
      future visitors.

### Evening

- [ ] **Write down what didn't land.** Confused HN comments, repeated
      "why is this different from X" questions, FAQs people asked that
      aren't in the README. These become v0.1.1 docs improvements.
- [ ] **Add a "Launch day learnings" section** to CHANGELOG.md if
      anything substantive emerged.

## T+1d to T+7d

- [ ] **Submit to Console.dev / Pointer.io / Cooper Press newsletters.**
      Each has a "submit your tool" form. Most are free; the response
      rate is real (~30%).
- [ ] **Cross-post the blog post** (`blog-post.md`) to dev.to, Hashnode,
      and your personal blog. Set canonical URL to your personal blog.
- [ ] **Publish a follow-up tweet** with a screenshot of an actual PR
      comment from a user (if any) or a real coupling pair the action
      surfaced in your own work that week.
- [ ] **Open one GitHub Discussion** asking users for "what coupling
      did couplingguard surface that you didn't know about?" — the
      stories are gold for future marketing.

## T+30d

- [ ] **Write a "What 30 days of coupling data shows" post** if you've
      collected interesting patterns from your own repo or open-source
      consumers.
- [ ] **Cut v0.1.1** with the docs improvements you noted on launch
      day. Use the same tag-and-approve flow from `RELEASE.md`.

## Channels worth skipping (for v0.1)

- ❌ Product Hunt — couplingguard isn't a SaaS, and Product Hunt's
      audience is closer to "no-code maker" than "platform engineer."
- ❌ Paid ads — premature for v0.1. Wait until you've validated the
      "people understand the value in one screenshot" hypothesis from
      free channels first.
- ❌ Conference talks — too slow for launch. Save for v0.3+ once
      you have user case studies.
