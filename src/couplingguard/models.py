from dataclasses import dataclass, field

# Alias coupling-core's exception classes so anything raised by the algorithm
# library (open_repo, get_commits, build_normalized_matrix) propagates through
# couplingguard's existing `except CouplingGuardError` / `except ShallowCloneError`
# catch boundaries. CouplingGuardError == CouplingCoreError as classes (same
# class object, just two names). Tests that catch couplingguard's names
# continue to work; new code can use either name interchangeably.
from coupling_core import CouplingCoreError as CouplingGuardError
from coupling_core import ShallowCloneError as ShallowCloneError  # noqa: PLC0414

__all__ = [
    "Config",
    "ConfigError",
    "CouplingGuardError",
    "CouplingPair",
    "GitHubAuthError",
    "PRAnalysis",
    "ShallowCloneError",
]


@dataclass
class Config:
    lookback_days: int = 90
    min_occurrences: int = 3
    max_pairs: int = 10
    low_threshold: float = 0.3
    high_threshold: float = 0.7
    fail_threshold: str | None = None
    exclude: list[str] = field(default_factory=list)
    dry_run: bool = False
    publish_dashboard: bool = False


@dataclass
class CouplingPair:
    file_in_pr: str
    coupled_file: str
    score: float
    co_changes: int
    total_commits: int
    risk: str
    suggested_owners: list[str] = field(default_factory=list)


@dataclass
class PRAnalysis:
    pr_number: int
    pr_files: list[str]
    pairs: list[CouplingPair]
    max_score: float
    pr_risk: str
    previous_max_score: float | None = None


# CouplingGuardError and ShallowCloneError are imported from coupling_core at
# the top of this file. ConfigError and GitHubAuthError remain couplingguard-
# specific subclasses — they're errors about couplingguard's surface area
# (YAML config, GitHub API auth), not about the algorithm itself.

class ConfigError(CouplingGuardError):
    """Raised when .couplingguard.yml or action inputs cannot be parsed."""


class GitHubAuthError(CouplingGuardError):
    """Raised when the GitHub token is missing or lacks required permissions."""
