from dataclasses import dataclass, field


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


class CouplingGuardError(Exception):
    """Base exception for all couplingguard runtime errors."""


class ShallowCloneError(CouplingGuardError):
    """Raised when the repo is a shallow clone and fetch-depth: 0 is needed."""


class ConfigError(CouplingGuardError):
    """Raised when .couplingguard.yml or action inputs cannot be parsed."""


class GitHubAuthError(CouplingGuardError):
    """Raised when the GitHub token is missing or lacks required permissions."""
