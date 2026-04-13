"""
intent_resolver.py
──────────────────
Core service: takes user query + context → calls LLM → parses + validates
response → returns structured result.
"""

import json
import logging
import re
from typing import Union

from app.ai.client import AIClient, Message
from app.models.request_models import (
    ConversationMessage,
    ResolveRequest,
    ResolvedResponse,
    AmbiguousResponse,
    ErrorResponse,
    FilterPayload,
    FilterOperation,
    Pagination,
    RuntimeContext,
)
from app.prompts.system_prompt import build_system_prompt
from app.services.validator import FilterValidator
from app.services.date_resolver import resolve_date_range_values
from app.schema.filter_schema import DEFAULT_COLUMNS

logger = logging.getLogger(__name__)

ResolveResult = Union[ResolvedResponse, AmbiguousResponse, ErrorResponse]


class IntentResolver:

    def __init__(self, ai_client: AIClient):
        self._client = ai_client
        self._validator = FilterValidator()

    async def resolve(self, request: ResolveRequest) -> ResolveResult:
        system_prompt = build_system_prompt(
            countries=request.context.countries,
            providers=request.context.providers,
        )

        # Build message history for LLM
        messages = self._build_messages(request)

        logger.info("Resolving query: '%s'", request.query)

        raw_response = await self._client.complete(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=1024,
            temperature=0.1,
        )

        return self._parse_and_validate(raw_response, request.conversation_history, request.query)

    # ── Private ───────────────────────────────────────────────────────────────

    def _build_messages(self, request: ResolveRequest) -> list[Message]:
        """Build the full conversation history to send to the LLM."""
        messages = []

        # Include previous turns for multi-step clarification
        for msg in request.conversation_history:
            messages.append(Message(role=msg.role, content=msg.content))

        # Append current query
        messages.append(Message(role="user", content=request.query))
        return messages

    def _parse_and_validate(
        self,
        raw: str,
        history: list[ConversationMessage],
        current_query: str,
    ) -> ResolveResult:
        """Parse LLM JSON output and validate against schema."""

        parsed = self._extract_json(raw)
        if parsed is None:
            logger.error("Failed to parse LLM response as JSON: %s", raw)
            return ErrorResponse(message="Failed to parse AI response. Please try again.")

        status = parsed.get("status")

        # ── Resolved ──────────────────────────────────────────────────────────
        if status == "resolved":
            try:
                payload_raw = parsed.get("payload", {})
                filters_raw = payload_raw.get("filters", [])
                columns = payload_raw.get("columns", DEFAULT_COLUMNS["DEFAULT"])
                pagination = payload_raw.get("pagination", {"limit": 100, "offset": 0})

                # Resolve semantic date tokens
                for f in filters_raw:
                    if f.get("type") == "dateRange":
                        f["values"] = resolve_date_range_values(f.get("values", []))

                # Validate and sanitize
                sanitized_filters = self._validator.validate_and_sanitize(filters_raw)
                sanitized_columns = self._validator.validate_columns(columns)

                payload = FilterPayload(
                    columns=sanitized_columns,
                    filters=[
                        FilterOperation(
                            key=f["key"],
                            type=f["type"],
                            values=f["values"],
                        )
                        for f in sanitized_filters
                    ],
                    pagination=Pagination(
                        limit=pagination.get("limit", 100),
                        offset=pagination.get("offset", 0),
                    ),
                )

                return ResolvedResponse(
                    payload=payload,
                    human_summary=parsed.get("human_summary", "Results"),
                )

            except Exception as e:
                logger.error("Error building resolved response: %s", e)
                return ErrorResponse(message="Failed to build filter payload. Please rephrase your query.")

        # ── Ambiguous ─────────────────────────────────────────────────────────
        if status == "ambiguous":
            updated_history = list(history) + [
                ConversationMessage(role="user", content=current_query),
                ConversationMessage(role="assistant", content=parsed.get("question", "")),
            ]

            return AmbiguousResponse(
                question=parsed.get("question", "Could you clarify your request?"),
                options=parsed.get("options", []),
                allow_custom=parsed.get("allow_custom", True),
                conversation_history=updated_history,
            )

        # ── Error ─────────────────────────────────────────────────────────────
        if status == "error":
            return ErrorResponse(message=parsed.get("message", "Unable to process this request."))

        # Unexpected status
        logger.warning("Unexpected status in LLM response: %s", status)
        return ErrorResponse(message="Unexpected AI response. Please try again.")

    def _extract_json(self, raw: str) -> dict | None:
        """
        Robustly extract JSON from LLM response.
        Handles cases where model wraps output in markdown fences despite instructions.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

        # Try direct parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try to extract first JSON object from the string
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None
