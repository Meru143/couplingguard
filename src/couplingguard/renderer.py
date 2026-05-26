from __future__ import annotations

import json

from .models import Config, CouplingPair, PRAnalysis

MARKER = "<!-- couplingguard:marker -->"
DATA_MARKER_TEMPLATE = "<!-- couplingguard:data:{payload} -->"

RISK_EMOJI: dict[str, str] = {"low": "🟢", "medium": "🟡", "high": "🔴"}
RISK_LABEL: dict[str, str] = {"low": "Low", "medium": "Medium", "high": "High"}

MAX_BODY_CHARS = 65000  # GitHub limit is 65536; leave headroom for truncation note
TRUNCATION_NOTE = (
    "\n\n_… and {extra} more pairs. Run couplingguard locally for the full report._"
)


def risk_emoji(risk: str) -> str:
    return RISK_EMOJI.get(risk, "⚪")


def _risk_for_score(score: float, config: Config) -> str:
    if score < config.low_threshold:
        return "low"
    if score < config.high_threshold:
        return "medium"
    return "high"


def render_table_row(pair: CouplingPair) -> str:
    emoji = risk_emoji(pair.risk)
    label = RISK_LABEL.get(pair.risk, pair.risk.title())
    return (
        f"| `{pair.file_in_pr}` | `{pair.coupled_file}` "
        f"| {pair.score:.2f} | {emoji} {label} "
        f"| {pair.co_changes}/{pair.total_commits} commits |"
    )


def _build_data_blob(analysis: PRAnalysis) -> str:
    scores: dict[str, float] = {}
    for pair in analysis.pairs:
        prev = scores.get(pair.file_in_pr, 0.0)
        if pair.score > prev:
            scores[pair.file_in_pr] = pair.score
    payload = json.dumps(
        {"max_score": analysis.max_score, "scores": scores},
        separators=(",", ":"),
        sort_keys=True,
    )
    return DATA_MARKER_TEMPLATE.format(payload=payload)


def _build_delta_line(analysis: PRAnalysis, config: Config) -> str | None:
    if analysis.previous_max_score is None:
        return None
    prev = analysis.previous_max_score
    curr = analysis.max_score
    if abs(prev - curr) < 1e-9:
        return None
    prev_risk = _risk_for_score(prev, config)
    curr_risk = _risk_for_score(curr, config)
    arrow = "↑" if curr > prev else "↓"
    return (
        f"> ⚠️ Score changed since last push: "
        f"{risk_emoji(prev_risk)} {prev:.2f} → {risk_emoji(curr_risk)} {curr:.2f} {arrow}"
    )


def _aggregate_reviewers(pairs: list[CouplingPair]) -> list[str]:
    aggregated: list[str] = []
    for pair in pairs:
        aggregated.extend(pair.suggested_owners)
    return list(dict.fromkeys(aggregated))


def _truncate_to_limit(body: str, pair_count: int) -> str:
    if len(body) <= MAX_BODY_CHARS:
        return body
    # Walk back through table rows, dropping from the end until we fit.
    lines = body.splitlines(keepends=True)
    while len("".join(lines)) > MAX_BODY_CHARS - len(TRUNCATION_NOTE.format(extra=999)) and lines:
        lines.pop()
    truncated = "".join(lines).rstrip()
    remaining_rows = sum(1 for ln in lines if ln.startswith("| `"))
    extra = max(pair_count - remaining_rows, 1)
    return truncated + TRUNCATION_NOTE.format(extra=extra)


def render_comment(analysis: PRAnalysis, config: Config) -> str:
    """Render the full PR comment body. Pure: no API or file I/O."""
    data_marker = _build_data_blob(analysis)

    if not analysis.pairs:
        return (
            f"{MARKER}\n"
            f"{data_marker}\n"
            "_No coupling patterns detected in this PR's changed files._"
        )

    headline = (
        f"🔍 couplingguard — {len(analysis.pairs)} "
        f"{'pair' if len(analysis.pairs) == 1 else 'pairs'} detected, "
        f"highest risk: {risk_emoji(analysis.pr_risk)} {analysis.max_score:.2f}"
    )

    sections: list[str] = [MARKER, data_marker, "<details>", f"<summary>{headline}</summary>", ""]

    delta = _build_delta_line(analysis, config)
    if delta is not None:
        sections.extend([delta, ""])

    sections.extend(
        [
            "| File in PR | Coupled With | Score | Risk | Co-changes |",
            "|------------|--------------|-------|------|------------|",
        ]
    )
    sections.extend(render_table_row(p) for p in analysis.pairs)

    reviewers = _aggregate_reviewers(analysis.pairs)
    if reviewers:
        sections.extend(
            [
                "",
                f"**Suggested reviewers for coupled files:** {', '.join(reviewers)}",
            ]
        )

    sections.extend(["", "</details>"])
    body = "\n".join(sections)
    return _truncate_to_limit(body, len(analysis.pairs))


def render_info_comment(reason: str) -> str:
    """Render a minimal informational comment for the shallow-clone /
    no-history / no-changed-files cases. Carries the marker so future
    runs can find and edit it like any other couplingguard comment.
    """
    return f"{MARKER}\nℹ️ couplingguard: {reason}"
