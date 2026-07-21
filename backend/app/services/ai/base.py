"""Modular AI provider interface.

Any provider (local Ollama today, a cloud model later) implements this
protocol so the rest of the app never depends on a specific vendor SDK.
"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a single completion for the given prompts."""
        raise NotImplementedError

    @abstractmethod
    async def is_available(self) -> bool:
        """Whether the provider is reachable/configured."""
        raise NotImplementedError
