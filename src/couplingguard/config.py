from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import Config, ConfigError

CONFIG_FILENAME = ".couplingguard.yml"

INT_FIELDS = ("lookback_days", "min_occurrences", "max_pairs")
FLOAT_FIELDS = ("low_threshold", "high_threshold")
BOOL_FIELDS = ("dry_run", "publish_dashboard")
STR_FIELDS = ("fail_threshold",)


def parse_action_inputs(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Read GitHub Actions INPUT_* env vars and return a dict of set values.

    Empty strings are treated as "not set" so YAML defaults still win for
    inputs the user did not pass. Type casting failures raise ConfigError
    with a message identifying the offending input.
    """
    src = env if env is not None else os.environ
    out: dict[str, Any] = {}

    def _get(name: str) -> str | None:
        raw = src.get(f"INPUT_{name.upper()}", "")
        return raw if raw != "" else None

    for name in INT_FIELDS:
        raw = _get(name)
        if raw is None:
            continue
        try:
            out[name] = int(raw)
        except ValueError as exc:
            raise ConfigError(
                f"couplingguard: Error — action input '{name}' must be an integer, got {raw!r}."
            ) from exc

    for name in FLOAT_FIELDS:
        raw = _get(name)
        if raw is None:
            continue
        try:
            out[name] = float(raw)
        except ValueError as exc:
            raise ConfigError(
                f"couplingguard: Error — action input '{name}' must be a number, got {raw!r}."
            ) from exc

    for name in BOOL_FIELDS:
        raw = _get(name)
        if raw is None:
            continue
        out[name] = raw.strip().lower() == "true"

    for name in STR_FIELDS:
        raw = _get(name)
        if raw is None:
            continue
        out[name] = raw

    raw_exclude = src.get("INPUT_EXCLUDE", "")
    if raw_exclude:
        out["exclude"] = [line.strip() for line in raw_exclude.splitlines() if line.strip()]

    return out


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = (mark.line + 1) if mark is not None else "?"
        raise ConfigError(
            f"couplingguard: Error — .couplingguard.yml is not valid YAML. Line {line}: {exc}"
        ) from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(
            "couplingguard: Error — .couplingguard.yml must be a mapping at the top level."
        )
    return loaded


def load_config(repo_root: Path, action_inputs: dict[str, Any] | None = None) -> Config:
    """Load and merge config with priority: defaults < YAML file < action inputs.

    The `exclude` field is merged (YAML list ++ action input list, dedup
    preserving insertion order) rather than overridden, because users
    typically want to add to project-level excludes from a workflow.
    """
    yaml_path = repo_root / CONFIG_FILENAME
    yaml_data: dict[str, Any] = _read_yaml(yaml_path) if yaml_path.exists() else {}

    inputs: dict[str, Any] = action_inputs if action_inputs is not None else {}

    yaml_exclude = list(yaml_data.get("exclude", []) or [])
    input_exclude = list(inputs.get("exclude", []) or [])
    merged_exclude = list(dict.fromkeys(yaml_exclude + input_exclude))

    fields: dict[str, Any] = {}
    for name in (*INT_FIELDS, *FLOAT_FIELDS, *BOOL_FIELDS, *STR_FIELDS):
        if name in inputs:
            fields[name] = inputs[name]
        elif name in yaml_data:
            fields[name] = yaml_data[name]
    fields["exclude"] = merged_exclude

    try:
        return Config(**fields)
    except TypeError as exc:
        raise ConfigError(
            f"couplingguard: Error — invalid config field: {exc}"
        ) from exc
