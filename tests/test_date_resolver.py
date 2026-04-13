"""
test_date_resolver.py
─────────────────────
Unit tests for semantic date token resolution.
"""

import pytest
from datetime import datetime, timedelta
from app.services.date_resolver import resolve_date_token, resolve_date_range_values

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def test_today_resolves_to_today():
    result = resolve_date_token("TODAY")
    today = datetime.now().strftime("%Y-%m-%d")
    assert result.startswith(today)


def test_yesterday_resolves_to_yesterday():
    result = resolve_date_token("YESTERDAY")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result.startswith(yesterday)


def test_last_7_days_resolves_correctly():
    result = resolve_date_token("LAST_7_DAYS")
    expected = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    assert result.startswith(expected)


def test_last_30_days_resolves_correctly():
    result = resolve_date_token("LAST_30_DAYS")
    expected = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    assert result.startswith(expected)


def test_this_month_resolves_to_first_of_month():
    result = resolve_date_token("THIS_MONTH")
    first_of_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    assert result.startswith(first_of_month)


def test_this_year_resolves_to_jan_first():
    result = resolve_date_token("THIS_YEAR")
    jan_first = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
    assert result.startswith(jan_first)


def test_non_token_passthrough():
    """Real date strings should pass through unchanged."""
    real_date = "2024-06-15 00:00:00"
    result = resolve_date_token(real_date)
    assert result == real_date


def test_unknown_token_passthrough():
    """Unknown tokens pass through unchanged — don't break silently."""
    result = resolve_date_token("SOME_RANDOM_TOKEN")
    assert result == "SOME_RANDOM_TOKEN"


def test_date_range_both_tokens():
    result = resolve_date_range_values(["LAST_7_DAYS", "TODAY"])
    assert len(result) == 2
    assert "LAST_7_DAYS" not in result[0]
    assert "TODAY" not in result[1]


def test_date_range_empty_end():
    result = resolve_date_range_values(["LAST_30_DAYS", ""])
    assert len(result) == 2
    assert result[1] == ""


def test_date_range_empty_input():
    result = resolve_date_range_values([])
    assert result == ["", ""]


def test_date_range_single_value():
    result = resolve_date_range_values(["LAST_7_DAYS"])
    assert len(result) == 2
    assert result[1] == ""


def test_case_insensitive_token():
    result_upper = resolve_date_token("TODAY")
    result_lower = resolve_date_token("today")
    result_mixed = resolve_date_token("Today")
    # All should resolve to same date
    assert result_upper[:10] == result_lower[:10] == result_mixed[:10]
