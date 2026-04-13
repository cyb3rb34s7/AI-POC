"""
factory.py
──────────
Returns the configured AIClient adapter based on settings.
Add new adapters here — nothing else in the codebase needs to change.
"""

from app.ai.client import AIClient
from config import settings


def get_ai_client() -> AIClient:
    adapter = settings.llm_adapter

    if adapter == "groq":
        from app.ai.adapters.groq_adapter import GroqAdapter
        return GroqAdapter()

    if adapter == "bedrock":
        from app.ai.adapters.bedrock_adapter import BedrockAdapter
        return BedrockAdapter()

    if adapter == "custom":
        from app.ai.adapters.custom_adapter import CustomLLMAdapter
        return CustomLLMAdapter()

    raise ValueError(
        f"Unknown LLM adapter: '{adapter}'. "
        f"Valid options: 'groq', 'bedrock', 'custom'"
    )
