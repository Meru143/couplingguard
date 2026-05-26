from __future__ import annotations

from couplingguard.delta import (
    DELTA_MARKER_PATTERN,
    extract_previous_data,
    get_previous_max_score,
)


def test_extract_valid_json_object() -> None:
    body = '<!-- couplingguard:data:{"max_score": 0.82, "scores": {"a.py": 0.82}} -->'
    data = extract_previous_data(body)
    assert data == {"max_score": 0.82, "scores": {"a.py": 0.82}}


def test_extract_malformed_json_returns_none() -> None:
    body = "<!-- couplingguard:data:{not valid} -->"
    assert extract_previous_data(body) is None


def test_extract_no_marker_returns_none() -> None:
    assert extract_previous_data("just a regular comment") is None
    assert extract_previous_data("") is None


def test_extract_empty_object_returns_empty_dict() -> None:
    assert extract_previous_data("<!-- couplingguard:data:{} -->") == {}


def test_extract_non_dict_payload_returns_none() -> None:
    # Top-level array is valid JSON but not the shape we expect.
    # Our regex requires `{...}` so this shouldn't even match — but the
    # defensive isinstance guard exists for the manually-edited case.
    body = '<!-- couplingguard:data:{"max_score": 0.5} -->'
    assert extract_previous_data(body) == {"max_score": 0.5}


def test_get_previous_max_score_extracts_float() -> None:
    body = '<!-- couplingguard:data:{"max_score": 0.82} -->'
    assert get_previous_max_score(body) == 0.82


def test_get_previous_max_score_no_marker_returns_none() -> None:
    assert get_previous_max_score("blank") is None


def test_get_previous_max_score_missing_field_returns_none() -> None:
    assert get_previous_max_score("<!-- couplingguard:data:{} -->") is None


def test_get_previous_max_score_non_numeric_returns_none() -> None:
    body = '<!-- couplingguard:data:{"max_score": "high"} -->'
    assert get_previous_max_score(body) is None


def test_get_previous_max_score_int_coerced_to_float() -> None:
    body = '<!-- couplingguard:data:{"max_score": 0} -->'
    assert get_previous_max_score(body) == 0.0


def test_marker_pattern_dotall() -> None:
    # Multi-line JSON should still match (re.DOTALL).
    multiline = '<!-- couplingguard:data:{\n  "max_score": 0.5\n} -->'
    assert DELTA_MARKER_PATTERN.search(multiline) is not None
    assert get_previous_max_score(multiline) == 0.5
