from app.services.ai.base import AIProvider


class DisabledProvider(AIProvider):
    """No-op provider used when AI_PROVIDER=disabled or no backend is configured."""

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError(
            "The AI assistant is not configured. Set AI_PROVIDER=ollama and "
            "OLLAMA_BASE_URL, or implement another AIProvider."
        )

    async def is_available(self) -> bool:
        return False
