import json
from abc import ABC, abstractmethod
from typing import Dict, Any


class AIProviderError(Exception):
    """Base exception for all AI provider-related errors."""
    pass


class AIConfigurationError(AIProviderError):
    """Exception raised for configuration errors in AI providers."""
    pass


class AICallError(AIProviderError):
    """Exception raised for issues during the execution/API call of an AI provider."""
    pass


class BaseAIProvider(ABC):
    """
    Abstract Base Class representing an AI Provider for content rewriting/summarization.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the provider with its specific configuration block.
        """
        self.config = config or {}
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validates that all necessary configuration keys and values are present.
        Raises AIConfigurationError if validation fails.
        """
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Sends a generation request to the provider with the given prompt.
        Returns the generated string text.
        Raises AICallError if the request/generation fails.
        """
        pass

    def rewrite(self, title: str, content: str) -> str:
        """
        A default implementation of rewrite using generate.
        """
        prompt = f"Title: {title}\nContent: {content}"
        return self.generate(prompt)
