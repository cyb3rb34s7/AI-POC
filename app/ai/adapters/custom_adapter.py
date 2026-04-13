"""
custom_adapter.py
─────────────────
Adapter for your internal LLM — generic HTTP POST.
Adjust request/response parsing to match your internal LLM's API contract.
"""

import logging
import httpx
from app.ai.client import AIClient, Message
from config import settings

logger = logging.getLogger(__name__)


class CustomLLMAdapter(AIClient):

    def __init__(self):
        self._url = settings.custom_llm_url
        self._api_key = settings.custom_llm_api_key
        self._timeout = 60.0

    @property
    def adapter_name(self) -> str:
        return "custom_llm"

    async def complete(
        self,
        system_prompt: str,
        messages: list[Message],
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # ── Adjust this payload shape to match your internal LLM's API ────────
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                *[{"role": m.role, "content": m.content} for m in messages],
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        logger.debug("Custom LLM request | url=%s", self._url)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # ── Adjust this to match your internal LLM's response shape ──────────
        # Common shapes:
        #   OpenAI-compatible: data["choices"][0]["message"]["content"]
        #   Custom:            data["response"] or data["output"] or data["text"]
        content = (
            data.get("choices", [{}])[0].get("message", {}).get("content")
            or data.get("response")
            or data.get("output")
            or data.get("text")
            or ""
        )

        if not content:
            raise RuntimeError(f"Custom LLM returned unexpected response shape: {data}")

        logger.debug("Custom LLM response: %s", content)
        return content
