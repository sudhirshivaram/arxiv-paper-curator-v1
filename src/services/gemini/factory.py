"""Factory for creating Gemini clients."""

from src.config import get_settings
from src.services.gemini.client import GeminiClient


def make_gemini_client() -> GeminiClient:
    """
    Create and return a Gemini client instance.

    Returns:
        GeminiClient: Configured Gemini client
    """
    settings = get_settings()
    return GeminiClient(settings)
