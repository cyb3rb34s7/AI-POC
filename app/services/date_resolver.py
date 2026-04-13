"""
date_resolver.py
────────────────
Converts semantic date tokens from LLM output into actual date strings
expected by the Java filter API.

Format: 'YYYY-MM-DD HH24:MI:SS' (matches Oracle TO_DATE format in mapper)
"""

from datetime import datetime, timedelta
from calendar import monthrange


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def resolve_date_token(token: str) -> str:
    """
    Convert a semantic date token to an actual date string.
    Returns the token unchanged if it's not a known semantic token
    (assumes it's already a real date string).
    """
    now = datetime.now()

    match token.upper():
        case "TODAY":
            return now.strftime(DATE_FORMAT)

        case "YESTERDAY":
            return (now - timedelta(days=1)).strftime(DATE_FORMAT)

        case "LAST_7_DAYS":
            return (now - timedelta(days=7)).strftime(DATE_FORMAT)

        case "LAST_30_DAYS":
            return (now - timedelta(days=30)).strftime(DATE_FORMAT)

        case "THIS_MONTH":
            return now.replace(day=1).strftime(DATE_FORMAT)

        case "LAST_MONTH":
            first_of_this_month = now.replace(day=1)
            last_month = first_of_this_month - timedelta(days=1)
            return last_month.replace(day=1).strftime(DATE_FORMAT)

        case "THIS_YEAR":
            return now.replace(month=1, day=1).strftime(DATE_FORMAT)

        case _:
            # Not a semantic token — return as-is (already a real date)
            return token


def resolve_date_range_values(values: list[str]) -> list[str]:
    """
    Resolve all values in a dateRange filter, converting any semantic
    tokens to actual date strings. Always returns a 2-element list.
    """
    if len(values) == 0:
        return ["", ""]
    if len(values) == 1:
        return [resolve_date_token(values[0]), ""]

    return [resolve_date_token(v) if v else "" for v in values[:2]]
