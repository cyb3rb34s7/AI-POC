"""
bedrock_adapter.py
──────────────────
AWS Bedrock adapter — supports Claude and other Bedrock models.
Uses boto3 async via run_in_executor since boto3 is sync-only.
"""

import json
import logging
import asyncio
from functools import partial
import boto3
from app.ai.client import AIClient, Message
from config import settings

logger = logging.getLogger(__name__)


class BedrockAdapter(AIClient):

    def __init__(self):
        self._client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self._model_id = settings.bedrock_model_id

    @property
    def adapter_name(self) -> str:
        return f"bedrock:{self._model_id}"

    async def complete(
        self,
        system_prompt: str,
        messages: list[Message],
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        # Run boto3 sync call in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(self._invoke, system_prompt, messages, max_tokens, temperature),
        )
        return response

    def _invoke(
        self,
        system_prompt: str,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
    ) -> str:
        # Claude on Bedrock uses the Messages API format
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        logger.debug("Bedrock request | model=%s", self._model_id)

        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        result = json.loads(response["body"].read())
        content = result["content"][0]["text"]
        logger.debug("Bedrock response: %s", content)
        return content
