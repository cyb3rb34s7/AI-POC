"""
conftest.py
───────────
Shared pytest fixtures used across all test modules.
"""

import pytest
from unittest.mock import AsyncMock
from app.ai.client import AIClient


class MockAIClient(AIClient):
    """Test double — inject any response string via set_response()."""

    def __init__(self):
        self._response = ""

    def set_response(self, response: str):
        self._response = response

    async def complete(self, system_prompt, messages, max_tokens=1024, temperature=0.1):
        return self._response

    @property
    def adapter_name(self) -> str:
        return "mock"


@pytest.fixture
def mock_ai_client():
    return MockAIClient()
