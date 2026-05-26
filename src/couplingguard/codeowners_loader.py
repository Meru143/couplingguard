from __future__ import annotations

import logging
from pathlib import Path

from codeowners import CodeOwners

from .models import CouplingPair

log = logging.getLogger(__name__)

CODEOWNERS_SEARCH_PATHS: tuple[str, ...] = (
    ".github/CODEOWNERS",
    "CODEOWNERS",
    "docs/CODEOWNERS",
)


def load_codeowners(repo_root: Path) -> CodeOwners | None:
    """Find and parse CODEOWNERS from the conventional locations.

    Returns None when no CODEOWNERS file is present (PRD E004) — the
    caller is expected to treat reviewer suggestions as a silent
    feature that simply doesn't run, not as an error.
    """
    for candidate in CODEOWNERS_SEARCH_PATHS:
        path = repo_root / candidate
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            log.debug("load_codeowners: parsed %s (%d bytes)", path, len(text))
            return CodeOwners(text)
    log.info("load_codeowners: no CODEOWNERS file found; reviewer suggestions skipped.")
    return None


def get_owners(codeowners: CodeOwners, file_path: str) -> list[str]:
    """Return owner strings for a file, flattening USERNAME and EMAIL types.

    Both @username and bare email forms are surfaced as-is so the
    rendered comment shows whatever the CODEOWNERS file declared.
    """
    matches = codeowners.of(file_path) or []
    return [owner for _kind, owner in matches]


def _dedup_preserve_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def suggest_reviewers(
    pairs: list[CouplingPair],
    codeowners: CodeOwners | None,
    pr_files: list[str],
) -> list[str]:
    """Attach suggested_owners to each pair and return a flat dedup'd list.

    For each pair, the coupled file's CODEOWNERS are computed, minus
    any owners already assigned to PR files (they're already involved
    in the review). Order is preserved as: pair-by-pair in score-desc
    order, owner-by-owner per pair.
    """
    if codeowners is None:
        for pair in pairs:
            pair.suggested_owners = []
        return []

    pr_file_owners: set[str] = set()
    for f in pr_files:
        pr_file_owners.update(get_owners(codeowners, f))

    aggregated: list[str] = []
    for pair in pairs:
        owners = [
            o for o in get_owners(codeowners, pair.coupled_file) if o not in pr_file_owners
        ]
        pair.suggested_owners = _dedup_preserve_order(owners)
        aggregated.extend(pair.suggested_owners)

    return _dedup_preserve_order(aggregated)
