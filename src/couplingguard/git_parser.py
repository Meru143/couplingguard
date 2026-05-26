from __future__ import annotations

import fnmatch
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import git

from .models import CouplingGuardError, ShallowCloneError

log = logging.getLogger(__name__)

BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".tiff", ".webp",
        ".whl", ".tar", ".gz", ".zip", ".7z", ".rar",
        ".lock", ".bin", ".so", ".dll", ".dylib", ".exe",
        ".pdf", ".woff", ".woff2", ".ttf", ".eot",
        ".mp3", ".mp4", ".mov", ".avi", ".webm",
    }
)

_RENAME_BRACE = re.compile(r"\{([^{}]*) => ([^{}]*)\}")
_OCTAL_ESCAPE = re.compile(rb"\\([0-7]{3})")


def open_repo(repo_path: Path) -> git.Repo:
    """Open a git repository, raising CouplingGuardError on invalid input
    and ShallowCloneError if fetch-depth: 0 was not configured.
    """
    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — not a git repository: {repo_path}"
        ) from exc
    except git.exc.NoSuchPathError as exc:
        raise CouplingGuardError(
            f"couplingguard: Error — path does not exist: {repo_path}"
        ) from exc

    if repo.git.rev_parse("--is-shallow-repository").strip() == "true":
        raise ShallowCloneError(
            "couplingguard: Error — repository is a shallow clone. "
            "Add 'fetch-depth: 0' to your checkout step."
        )

    return repo


def _decode_unicode_path(path: str) -> str:
    """Decode git's quoted-octal-escape format (e.g. "caf\\303\\251.py")
    used for non-ASCII filenames. Plain paths pass through unchanged.
    """
    if not (path.startswith('"') and path.endswith('"') and "\\" in path):
        return path
    inner = path[1:-1]
    as_bytes = inner.encode("latin-1", errors="replace")
    decoded_bytes = _OCTAL_ESCAPE.sub(lambda m: bytes([int(m.group(1), 8)]), as_bytes)
    try:
        return decoded_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return decoded_bytes.decode("utf-8", errors="replace")


def _normalize_rename(path: str) -> str:
    """Resolve git's '{old => new}' rename notation to the new path.

    Examples:
        src/{old.py => new.py}        -> src/new.py
        {old/dir => new/dir}/file.py  -> new/dir/file.py
        old.py => new.py              -> new.py
    Anything without the marker passes through unchanged.
    """
    if " => " not in path:
        return path

    def _replace(match: re.Match[str]) -> str:
        return match.group(2)

    if "{" in path and "}" in path:
        return _RENAME_BRACE.sub(_replace, path)

    return path.split(" => ", 1)[1]


def _is_binary(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in BINARY_EXTENSIONS


def apply_excludes(files: list[str], exclude_patterns: list[str]) -> list[str]:
    if not exclude_patterns:
        return files
    return [f for f in files if not any(fnmatch.fnmatch(f, p) for p in exclude_patterns)]


def _normalize_files(raw_files: list[str], exclude_patterns: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in raw_files:
        decoded = _decode_unicode_path(raw)
        resolved = _normalize_rename(decoded)
        if _is_binary(resolved):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(resolved)
    return apply_excludes(out, exclude_patterns)


def get_commits(
    repo: git.Repo,
    lookback_days: int,
    exclude_patterns: list[str] | None = None,
) -> list[list[str]]:
    """Walk HEAD's history within the lookback window and return one
    file list per non-merge commit.

    Binary files, files matching exclude_patterns, and empty commits
    are filtered out. Renames are resolved to the new path so the same
    file accumulates co-change counts across its history.
    """
    since = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    patterns = exclude_patterns or []

    out: list[list[str]] = []
    for commit in repo.iter_commits(rev="HEAD", no_merges=True, since=since):
        raw_files = [str(k) for k in commit.stats.files]
        if not raw_files:
            continue
        normalized = _normalize_files(raw_files, patterns)
        if normalized:
            out.append(normalized)

    log.debug("get_commits: %d commits in last %d days", len(out), lookback_days)
    return out


def get_file_commit_counts(commits: list[list[str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for files in commits:
        for f in files:
            counts[f] += 1
    return dict(counts)
