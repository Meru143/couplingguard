from __future__ import annotations

import json
import logging
import re
from typing import Any

log = logging.getLogger(__name__)

DELTA_MARKER_PATTERN = re.compile(
    r"<!-- couplingguard:data:({.*?}) -->", re.DOTALL
)


def extract_previous_data(comment_body: str) -> dict[str, Any] | None:
    """Pull the hidden JSON blob from a prior couplingguard PR comment.

    Returns None if the marker is missing or if the JSON is malformed
    (PRD edge case 10) — a manually-edited comment must never crash
    the run.
    """
    if not comment_body:
        return None
    match = DELTA_MARKER_PATTERN.search(comment_body)
    if match is None:
        return None
    raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning(
            "extract_previous_data: malformed JSON in delta marker (%s); skipping delta. payload=%r",
            exc,
            raw,
        )
        return None
    if not isinstance(data, dict):
        log.warning("extract_previous_data: delta payload is not an object; skipping delta.")
        return None
    return data


def get_previous_max_score(comment_body: str) -> float | None:
    """Convenience wrapper: returns the previous run's max_score, or None
    if the comment has no recoverable delta data.
    """
    data = extract_previous_data(comment_body)
    if data is None:
        return None
    value = data.get("max_score")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        log.warning(
            "get_previous_max_score: max_score field %r not coercible to float; skipping delta.",
            value,
        )
        return None
