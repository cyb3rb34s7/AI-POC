"""
groq_adapter.py
───────────────
Groq API adapter — uses llama-3.3-70b-versatile by default.
Good for testing: fast, cheap, capable enough for slot-filling tasks.
"""

import logging
from groq import AsyncGroq
from app.ai.client import AIClient, Message
from config import settings

logger = logging.getLogger(__name__)


class GroqAdapter(AIClient):

    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    @property
    def adapter_name(self) -> str:
        return f"groq:{self._model}"

    async def complete(
        self,
        system_prompt: str,
        messages: list[Message],
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        formatted = [{"role": "system", "content": system_prompt}]
        formatted += [{"role": m.role, "content": m.content} for m in messages]

        logger.debug("Groq request | model=%s | messages=%d", self._model, len(formatted))

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=formatted,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        content = response.choices[0].message.content
        logger.debug("Groq response: %s", content)
        return content
