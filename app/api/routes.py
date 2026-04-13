"""
routes.py
─────────
Three endpoints:
  POST /ai/resolve  — NL query → resolved payload or clarification
  POST /ai/execute  — confirmed payload → proxy to Java backend
  GET  /ai/health   — health check
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx

from app.ai.factory import get_ai_client
from app.services.intent_resolver import IntentResolver
from app.services.filter_proxy import FilterProxy
from app.models.request_models import (
    ResolveRequest,
    ExecuteRequest,
    ResolvedResponse,
    AmbiguousResponse,
    ErrorResponse,
    HealthResponse,
)
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Filter"])


@router.post("/resolve")
async def resolve_query(request: ResolveRequest):
    """
    Convert a natural language query into a filter API payload.

    Returns one of:
    - ResolvedResponse: ready to execute
    - AmbiguousResponse: needs clarification (includes options for UI chips)
    - ErrorResponse: unresolvable query
    """
    try:
        client = get_ai_client()
        resolver = IntentResolver(ai_client=client)
        result = await resolver.resolve(request)
        return result

    except Exception as e:
        logger.exception("Unexpected error in /resolve: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during resolution.")


@router.post("/execute")
async def execute_filter(request: ExecuteRequest):
    """
    Forward a confirmed filter payload to the Java backend.
    Returns the raw Java response so Angular can render it
    with the existing table component.
    """
    try:
        proxy = FilterProxy()
        result = await proxy.execute(request.payload)
        return JSONResponse(content=result)

    except httpx.HTTPStatusError as e:
        logger.error("Java backend error: %s", e.response.text)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Backend error: {e.response.text}",
        )
    except httpx.RequestError as e:
        logger.error("Could not reach Java backend: %s", e)
        raise HTTPException(status_code=503, detail="Could not reach content backend.")
    except Exception as e:
        logger.exception("Unexpected error in /execute: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during execution.")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check — confirms service is up and shows active adapter."""
    try:
        client = get_ai_client()
        return HealthResponse(status="ok", adapter=client.adapter_name)
    except Exception as e:
        return HealthResponse(status=f"degraded: {e}", adapter="unknown")
