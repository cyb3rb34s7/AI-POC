from pydantic import BaseModel, Field
from typing import Any, Literal, Optional


# ─── Inbound ───────────────────────────────────────────────────────────────────

class RuntimeContext(BaseModel):
    """Dynamic lists fetched by Angular at component load time."""
    countries: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ResolveRequest(BaseModel):
    query: str
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    context: RuntimeContext = Field(default_factory=RuntimeContext)


class ExecuteRequest(BaseModel):
    payload: dict[str, Any]


# ─── Filter API body (mirrors Java backend contract) ──────────────────────────

class FilterOperation(BaseModel):
    key: str
    type: Literal["filter", "search", "dateRange"]
    values: list[str]


class Pagination(BaseModel):
    limit: int = 100
    offset: int = 0


class FilterPayload(BaseModel):
    columns: list[str]
    filters: list[FilterOperation]
    pagination: Pagination = Field(default_factory=Pagination)


# ─── Outbound ─────────────────────────────────────────────────────────────────

class ResolvedResponse(BaseModel):
    status: Literal["resolved"] = "resolved"
    payload: FilterPayload
    human_summary: str


class AmbiguousResponse(BaseModel):
    status: Literal["ambiguous"] = "ambiguous"
    question: str
    options: list[str]
    allow_custom: bool = True
    conversation_history: list[ConversationMessage]


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str


class HealthResponse(BaseModel):
    status: str
    adapter: str
