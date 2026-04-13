"""
test_intent_resolver.py
───────────────────────
Unit tests for IntentResolver — mocks the AI client,
tests all response paths: resolved, ambiguous, error, malformed.
"""

import json
import pytest
from app.services.intent_resolver import IntentResolver
from app.models.request_models import (
    ResolveRequest,
    ResolvedResponse,
    AmbiguousResponse,
    ErrorResponse,
    RuntimeContext,
    ConversationMessage,
)
from tests.conftest import MockAIClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_request(query: str, history=None, countries=None, providers=None) -> ResolveRequest:
    return ResolveRequest(
        query=query,
        conversation_history=history or [],
        context=RuntimeContext(
            countries=countries or ["IN", "US", "KR"],
            providers=providers or ["Sony", "Viacom", "Disney"],
        ),
    )


def resolved_llm_response(filters: list, summary: str = "Test summary", columns=None) -> str:
    return json.dumps({
        "status": "resolved",
        "payload": {
            "columns": columns or ["CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS", "TYPE"],
            "filters": filters,
            "pagination": {"limit": 100, "offset": 0},
        },
        "human_summary": summary,
    })


def ambiguous_llm_response(question: str, options: list, allow_custom=True) -> str:
    return json.dumps({
        "status": "ambiguous",
        "question": question,
        "options": options,
        "allow_custom": allow_custom,
    })


def error_llm_response(message: str) -> str:
    return json.dumps({"status": "error", "message": message})


# ── Resolved response tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_simple_status_filter(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "TYPE", "type": "filter", "values": ["EPISODE"]},
            {"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["Ready For QC"]},
        ],
        summary="Episodes with status Ready For QC",
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me all episodes in Ready For QC"))

    assert isinstance(result, ResolvedResponse)
    assert result.human_summary == "Episodes with status Ready For QC"
    keys = [f.key for f in result.payload.filters]
    assert "TYPE" in keys
    assert "ASSET_CURRENT_STATUS" in keys


@pytest.mark.asyncio
async def test_resolve_show_title_and_type(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "TYPE", "type": "filter", "values": ["EPISODE"]},
            {"key": "SHOW_TITLE", "type": "search", "values": ["Mirzapur"]},
            {"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["QC Fail"]},
        ],
        summary="Episodes of Mirzapur with status QC Fail",
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Mirzapur episodes that failed QC"))

    assert isinstance(result, ResolvedResponse)
    keys = [f.key for f in result.payload.filters]
    assert "SHOW_TITLE" in keys
    assert "TYPE" in keys
    show_filter = next(f for f in result.payload.filters if f.key == "SHOW_TITLE")
    assert show_filter.values == ["Mirzapur"]


@pytest.mark.asyncio
async def test_resolve_multiple_status_values(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["QC Pass", "Temp QC Pass"]},
        ],
        summary="Content with QC Pass or Temp QC Pass",
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Content that passed QC"))

    assert isinstance(result, ResolvedResponse)
    status_filter = next(f for f in result.payload.filters if f.key == "ASSET_CURRENT_STATUS")
    assert "QC Pass" in status_filter.values


@pytest.mark.asyncio
async def test_resolve_date_range_with_semantic_token(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "ASSET_INGESTION_RANGE", "type": "dateRange", "values": ["LAST_7_DAYS", "TODAY"]},
        ],
        summary="Content ingested in the last 7 days",
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me content ingested last week"))

    assert isinstance(result, ResolvedResponse)
    date_filter = next(f for f in result.payload.filters if f.key == "ASSET_INGESTION_RANGE")
    # Semantic tokens should be resolved to actual date strings
    assert "LAST_7_DAYS" not in date_filter.values[0]
    assert "TODAY" not in date_filter.values[1]
    # Should be real date format
    assert "-" in date_filter.values[0]


@pytest.mark.asyncio
async def test_resolve_provider_filter(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "VC_CP_NM", "type": "filter", "values": ["Sony"]},
        ],
        summary="All content from Sony",
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me Sony content"))

    assert isinstance(result, ResolvedResponse)
    provider_filter = next(f for f in result.payload.filters if f.key == "VC_CP_NM")
    assert provider_filter.values == ["Sony"]


@pytest.mark.asyncio
async def test_resolve_country_filter(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "TYPE", "type": "filter", "values": ["MOVIE"]},
            {"key": "CNTY_CD", "type": "filter", "values": ["IN"]},
        ],
        summary="Movies in India",
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Movies available in India"))

    assert isinstance(result, ResolvedResponse)
    country_filter = next(f for f in result.payload.filters if f.key == "CNTY_CD")
    assert "IN" in country_filter.values


@pytest.mark.asyncio
async def test_resolve_pagination_defaults(mock_ai_client):
    mock_ai_client.set_response(resolved_llm_response(
        filters=[{"key": "TYPE", "type": "filter", "values": ["MOVIE"]}],
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show all movies"))

    assert isinstance(result, ResolvedResponse)
    assert result.payload.pagination.limit == 100
    assert result.payload.pagination.offset == 0


# ── Ambiguous response tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ambiguous_season_clarification(mock_ai_client):
    mock_ai_client.set_response(ambiguous_llm_response(
        question="Which season of Mirzapur are you looking for?",
        options=["Season 1", "Season 2", "Season 3", "All seasons"],
        allow_custom=True,
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me Mirzapur episodes"))

    assert isinstance(result, AmbiguousResponse)
    assert "Mirzapur" in result.question
    assert len(result.options) == 4
    assert result.allow_custom is True


@pytest.mark.asyncio
async def test_ambiguous_content_type_clarification(mock_ai_client):
    mock_ai_client.set_response(ambiguous_llm_response(
        question="What type of content are you looking for?",
        options=["EPISODE", "MOVIE", "SHOW", "SEASON", "SINGLEVOD", "MUSIC"],
        allow_custom=False,
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me all content"))

    assert isinstance(result, AmbiguousResponse)
    assert result.allow_custom is False
    assert "EPISODE" in result.options


@pytest.mark.asyncio
async def test_ambiguous_builds_conversation_history(mock_ai_client):
    mock_ai_client.set_response(ambiguous_llm_response(
        question="Which season?",
        options=["Season 1", "Season 2"],
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Mirzapur episodes"))

    assert isinstance(result, AmbiguousResponse)
    # History should include user query + assistant question
    assert len(result.conversation_history) == 2
    assert result.conversation_history[0].role == "user"
    assert result.conversation_history[0].content == "Mirzapur episodes"
    assert result.conversation_history[1].role == "assistant"
    assert result.conversation_history[1].content == "Which season?"


@pytest.mark.asyncio
async def test_ambiguous_appends_to_existing_history(mock_ai_client):
    existing_history = [
        ConversationMessage(role="user", content="Mirzapur episodes"),
        ConversationMessage(role="assistant", content="Which season?"),
    ]

    mock_ai_client.set_response(ambiguous_llm_response(
        question="Which status are you filtering by?",
        options=["Ready For QC", "QC Fail", "Released"],
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(
        make_request("Season 2", history=existing_history)
    )

    assert isinstance(result, AmbiguousResponse)
    assert len(result.conversation_history) == 4


# ── Error response tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_response_passthrough(mock_ai_client):
    mock_ai_client.set_response(error_llm_response(
        "This query is not related to content management."
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("What's the weather in Mumbai?"))

    assert isinstance(result, ErrorResponse)
    assert "content management" in result.message


# ── Validation / sanitization tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_hallucinated_filter_key_is_dropped(mock_ai_client):
    """LLM invents a key that doesn't exist in schema — should be silently dropped."""
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "TYPE", "type": "filter", "values": ["EPISODE"]},
            {"key": "FAKE_KEY_HALLUCINATED", "type": "filter", "values": ["something"]},
        ],
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show episodes"))

    assert isinstance(result, ResolvedResponse)
    keys = [f.key for f in result.payload.filters]
    assert "FAKE_KEY_HALLUCINATED" not in keys
    assert "TYPE" in keys


@pytest.mark.asyncio
async def test_invalid_status_value_is_corrected(mock_ai_client):
    """LLM returns wrong casing — validator should correct to canonical form."""
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            {"key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["ready for qc"]},
        ],
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Ready for QC content"))

    assert isinstance(result, ResolvedResponse)
    status_filter = next(f for f in result.payload.filters if f.key == "ASSET_CURRENT_STATUS")
    assert "Ready For QC" in status_filter.values


@pytest.mark.asyncio
async def test_wrong_filter_type_is_corrected(mock_ai_client):
    """LLM uses wrong type for a key — validator corrects to schema-defined type."""
    mock_ai_client.set_response(resolved_llm_response(
        filters=[
            # SHOW_TITLE should be "search" but LLM says "filter"
            {"key": "SHOW_TITLE", "type": "filter", "values": ["Mirzapur"]},
        ],
    ))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Mirzapur"))

    assert isinstance(result, ResolvedResponse)
    show_filter = next(f for f in result.payload.filters if f.key == "SHOW_TITLE")
    assert show_filter.type == "search"


# ── Malformed LLM response tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_malformed_json_returns_error(mock_ai_client):
    mock_ai_client.set_response("I cannot process this request at the moment.")

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me content"))

    assert isinstance(result, ErrorResponse)


@pytest.mark.asyncio
async def test_json_wrapped_in_markdown_fences(mock_ai_client):
    """Some models wrap JSON in markdown fences despite instructions — should still parse."""
    raw = "```json\n" + resolved_llm_response(
        filters=[{"key": "TYPE", "type": "filter", "values": ["MOVIE"]}],
        summary="All movies",
    ) + "\n```"
    mock_ai_client.set_response(raw)

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show all movies"))

    assert isinstance(result, ResolvedResponse)
    assert result.human_summary == "All movies"


@pytest.mark.asyncio
async def test_unexpected_status_returns_error(mock_ai_client):
    mock_ai_client.set_response(json.dumps({"status": "unknown_status", "data": {}}))

    resolver = IntentResolver(mock_ai_client)
    result = await resolver.resolve(make_request("Show me content"))

    assert isinstance(result, ErrorResponse)
