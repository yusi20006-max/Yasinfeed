from typing import Dict, Any
from yasinfeed.rewrite.providers.base import BaseAIProvider


class DummyProvider(BaseAIProvider):
    """
    A lightweight mock provider that echoes inputs or returns standard mock responses.
    Useful for testing, development, and offline dry-runs.
    """

    def validate_config(self) -> None:
        # Dummy provider doesn't strictly require any configuration.
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        prefix = self.config.get("prefix", "[Dummy AI]")
        return f"{prefix} processed prompt: {prompt}"
