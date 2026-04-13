"""
client.py
─────────
Abstract base class for all LLM adapters.
Every adapter must implement the `complete` method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    role: str   # "user" | "assistant" | "system"
    content: str


class AIClient(ABC):
    """
    Provider-agnostic LLM interface.
    Swap adapters via config — the service layer never changes.
    """

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        messages: list[Message],
        max_tokens: int = 1024,
        temperature: float = 0.1,   # Low temp for deterministic JSON output
    ) -> str:
        """
        Send a completion request and return the raw text response.
        Raises RuntimeError on failure.
        """
        ...

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Human-readable name for health check and logging."""
        ...
