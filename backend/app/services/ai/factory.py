from functools import lru_cache

from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.disabled_provider import DisabledProvider
from app.services.ai.ollama_provider import OllamaProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER == "ollama":
        return OllamaProvider()
    return DisabledProvider()
