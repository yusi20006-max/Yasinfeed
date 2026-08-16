from typing import Dict, Any, Type
from yasinfeed.rewrite.providers.base import BaseAIProvider, AIConfigurationError
from yasinfeed.rewrite.providers.dummy import DummyProvider
from yasinfeed.rewrite.providers.openai import OpenAIProvider
from yasinfeed.rewrite.providers.huggingface import HuggingFaceProvider
from yasinfeed.rewrite.pipeline_providers import MockAIProvider
from yasinfeed.rewrite.providers.yasinai_provider import YasinAIProvider

# Mapping of provider identifiers to their concrete class implementations.
PROVIDERS: Dict[str, Type[BaseAIProvider]] = {
    "dummy": DummyProvider,
    "openai": OpenAIProvider,
    "huggingface": HuggingFaceProvider,
    "mock_ai": MockAIProvider,
    "yasinai": YasinAIProvider,
    "yasin-ai": YasinAIProvider,
}


def create_provider(provider_name: str, config: Dict[str, Any]) -> BaseAIProvider:
    """
    Factory function to instantiate the correct AI provider class based on its name.
    """
    name_lower = (provider_name or "").strip().lower()
    if name_lower not in PROVIDERS:
        raise AIConfigurationError(
            f"Unsupported AI provider: '{provider_name}'. Supported providers: {list(PROVIDERS.keys())}"
        )

    provider_cls = PROVIDERS[name_lower]
    return provider_cls(config)
