from __future__ import annotations

from pathlib import Path

import pytest

from couplingguard.config import load_config, parse_action_inputs
from couplingguard.models import Config, ConfigError


def test_missing_yaml_uses_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path, {})
    assert cfg == Config()
    assert cfg.lookback_days == 90
    assert cfg.min_occurrences == 3
    assert cfg.exclude == []


def test_yaml_file_loaded(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text(
        "lookback_days: 180\nmin_occurrences: 5\nexclude:\n  - docs/**\n  - '*.md'\n"
    )
    cfg = load_config(tmp_path, {})
    assert cfg.lookback_days == 180
    assert cfg.min_occurrences == 5
    assert cfg.exclude == ["docs/**", "*.md"]


def test_action_input_overrides_yaml(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text("lookback_days: 180\n")
    cfg = load_config(tmp_path, {"lookback_days": 30})
    assert cfg.lookback_days == 30


def test_exclude_is_merged_not_overridden(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text("exclude:\n  - docs/**\n")
    cfg = load_config(tmp_path, {"exclude": ["*.md", "docs/**"]})
    # Dedup preserves insertion order: YAML first, then new entries
    assert cfg.exclude == ["docs/**", "*.md"]


def test_invalid_yaml_raises_config_error_with_line_number(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text("lookback_days: [unclosed\nmin_occurrences: 3\n")
    with pytest.raises(ConfigError) as exc:
        load_config(tmp_path, {})
    assert "Line" in str(exc.value)


def test_top_level_not_mapping_raises(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text("- this\n- is\n- a\n- list\n")
    with pytest.raises(ConfigError):
        load_config(tmp_path, {})


def test_fail_threshold_loaded(tmp_path: Path) -> None:
    (tmp_path / ".couplingguard.yml").write_text("fail_threshold: high\n")
    cfg = load_config(tmp_path, {})
    assert cfg.fail_threshold == "high"


def test_parse_action_inputs_basic() -> None:
    env = {
        "INPUT_LOOKBACK_DAYS": "120",
        "INPUT_MIN_OCCURRENCES": "5",
        "INPUT_DRY_RUN": "true",
        "INPUT_EXCLUDE": "docs/**\n*.md\n\n  migrations/**  \n",
        "INPUT_FAIL_THRESHOLD": "high",
        "INPUT_LOW_THRESHOLD": "0.25",
    }
    parsed = parse_action_inputs(env)
    assert parsed["lookback_days"] == 120
    assert parsed["min_occurrences"] == 5
    assert parsed["dry_run"] is True
    assert parsed["fail_threshold"] == "high"
    assert parsed["low_threshold"] == 0.25
    assert parsed["exclude"] == ["docs/**", "*.md", "migrations/**"]


def test_parse_action_inputs_empty_means_unset() -> None:
    env = {"INPUT_LOOKBACK_DAYS": "", "INPUT_DRY_RUN": ""}
    parsed = parse_action_inputs(env)
    assert "lookback_days" not in parsed
    assert "dry_run" not in parsed


def test_parse_action_inputs_bad_int_raises() -> None:
    with pytest.raises(ConfigError) as exc:
        parse_action_inputs({"INPUT_LOOKBACK_DAYS": "abc"})
    assert "integer" in str(exc.value)


def test_parse_action_inputs_bad_float_raises() -> None:
    with pytest.raises(ConfigError) as exc:
        parse_action_inputs({"INPUT_LOW_THRESHOLD": "not a number"})
    assert "number" in str(exc.value)


def test_dry_run_case_insensitive() -> None:
    for val in ("true", "TRUE", "True"):
        parsed = parse_action_inputs({"INPUT_DRY_RUN": val})
        assert parsed["dry_run"] is True
    parsed_false = parse_action_inputs({"INPUT_DRY_RUN": "false"})
    assert parsed_false["dry_run"] is False
