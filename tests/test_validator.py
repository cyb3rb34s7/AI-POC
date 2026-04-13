"""
test_validator.py
─────────────────
Unit tests for FilterValidator — schema enforcement, value sanitization.
"""

import pytest
from app.services.validator import FilterValidator


@pytest.fixture
def validator():
    return FilterValidator()


def test_valid_filter_passes_through(validator):
    filters = [{"key": "TYPE", "type": "filter", "values": ["EPISODE"]}]
    result = validator.validate_and_sanitize(filters)
    assert len(result) == 1
    assert result[0]["key"] == "TYPE"


def test_unknown_key_is_dropped(validator):
    filters = [
        {"key": "VALID_TYPE", "type": "filter", "values": ["EPISODE"]},
        {"key": "NONEXISTENT_KEY", "type": "filter", "values": ["foo"]},
    ]
    # Only the known key should survive
    result = validator.validate_and_sanitize(filters)
    keys = [r["key"] for r in result]
    assert "NONEXISTENT_KEY" not in keys


def test_invalid_enum_value_is_dropped(validator):
    filters = [{"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["FAKE_STATUS"]}]
    result = validator.validate_and_sanitize(filters)
    # All values invalid → entire filter dropped
    assert len(result) == 0


def test_mixed_valid_invalid_values(validator):
    filters = [{
        "key": "ASSET_CURRENT_STATUS",
        "type": "filter",
        "values": ["Released", "FAKE_STATUS", "QC Fail"],
    }]
    result = validator.validate_and_sanitize(filters)
    assert len(result) == 1
    assert "Released" in result[0]["values"]
    assert "FAKE_STATUS" not in result[0]["values"]
    assert "QC Fail" in result[0]["values"]


def test_case_insensitive_value_correction(validator):
    filters = [{"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["released"]}]
    result = validator.validate_and_sanitize(filters)
    assert result[0]["values"] == ["Released"]


def test_wrong_type_is_corrected_to_schema_type(validator):
    # SHOW_TITLE is "search" in schema, not "filter"
    filters = [{"key": "SHOW_TITLE", "type": "filter", "values": ["Mirzapur"]}]
    result = validator.validate_and_sanitize(filters)
    assert result[0]["type"] == "search"


def test_search_key_with_free_text_passes(validator):
    filters = [{"key": "SHOW_TITLE", "type": "search", "values": ["Sacred Games"]}]
    result = validator.validate_and_sanitize(filters)
    assert len(result) == 1
    assert result[0]["values"] == ["Sacred Games"]


def test_date_range_key_passes_through(validator):
    filters = [{"key": "ASSET_INGESTION_RANGE", "type": "dateRange", "values": ["2024-01-01 00:00:00", "2024-01-31 00:00:00"]}]
    result = validator.validate_and_sanitize(filters)
    assert len(result) == 1


def test_all_status_values_are_valid(validator):
    all_statuses = [
        "Ready For QC", "QC in Progress", "QC Pass", "Temp QC Pass",
        "QC Fail", "Ready for Release", "Released", "Untrackable", "Revoked",
    ]
    filters = [{"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": all_statuses}]
    result = validator.validate_and_sanitize(filters)
    assert len(result[0]["values"]) == len(all_statuses)


def test_all_content_types_are_valid(validator):
    all_types = ["EPISODE", "MOVIE", "SINGLEVOD", "MUSIC", "SHOW", "SEASON"]
    filters = [{"key": "TYPE", "type": "filter", "values": all_types}]
    result = validator.validate_and_sanitize(filters)
    assert len(result[0]["values"]) == len(all_types)


def test_column_validation_blocks_sql_keywords(validator):
    columns = ["CONTENT_ID", "MAIN_TITLE", "DROP", "DELETE", "ASSET_CURRENT_STATUS"]
    result = validator.validate_columns(columns)
    assert "DROP" not in result
    assert "DELETE" not in result
    assert "CONTENT_ID" in result


def test_empty_filters_returns_empty(validator):
    result = validator.validate_and_sanitize([])
    assert result == []
