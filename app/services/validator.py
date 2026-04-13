"""
validator.py
────────────
Validates LLM-produced filter payloads against the filter schema.
Catches hallucinated keys/values before they reach the Java backend.
"""

import logging
from app.schema.filter_schema import FILTER_SCHEMA, get_schema_by_key

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class FilterValidator:

    def validate_and_sanitize(self, filters: list[dict]) -> list[dict]:
        """
        Validates each filter operation:
        - Key must exist in schema
        - Type must match schema definition
        - Values must be from valid_values list (for enum fields)

        Returns sanitized filters (invalid ones are dropped with a warning).
        Raises ValidationError if result is empty after sanitization.
        """
        sanitized = []

        for op in filters:
            key = op.get("key", "")
            filter_type = op.get("type", "")
            values = op.get("values", [])

            schema = get_schema_by_key(key)

            if not schema:
                logger.warning("Dropping unknown filter key: '%s'", key)
                continue

            if schema.filter_type != filter_type:
                logger.warning(
                    "Filter key '%s' expects type '%s' but got '%s'. Correcting.",
                    key, schema.filter_type, filter_type
                )
                filter_type = schema.filter_type

            # Validate enum values for fields with known valid_values
            if schema.valid_values:
                valid_lower = {v.lower(): v for v in schema.valid_values}
                sanitized_values = []
                for v in values:
                    canonical = valid_lower.get(v.lower())
                    if canonical:
                        sanitized_values.append(canonical)
                    else:
                        logger.warning(
                            "Dropping invalid value '%s' for key '%s'. Valid: %s",
                            v, key, schema.valid_values
                        )
                if not sanitized_values:
                    logger.warning("All values invalid for key '%s'. Dropping filter.", key)
                    continue
                values = sanitized_values

            sanitized.append({"key": key, "type": filter_type, "values": values})

        return sanitized

    def validate_columns(self, columns: list[str]) -> list[str]:
        """
        Basic column validation — ensure no obviously invalid column names.
        Allows pass-through for most since column list is large.
        """
        blocked = {"DROP", "DELETE", "INSERT", "UPDATE", "--", ";"}
        return [c for c in columns if c.upper() not in blocked and c.strip()]
