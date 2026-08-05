from abc import ABC, abstractmethod
from typing import Dict, Any
from yasinfeed.rewrite.providers.base import BaseAIProvider

class BaseProvider(ABC):
    """
    Abstract base class for all content rewrite and transformation providers.
    """
    @abstractmethod
    def rewrite(self, title: str, content: str) -> str:
        """
        Rewrite or transform the given content and return the result.
        """
        pass


class DummyProvider(BaseProvider):
    """
    Dummy provider mimicking existing simple placeholder rewrite logic.
    """
    def rewrite(self, title: str, content: str) -> str:
        return f"[Rewritten by YasinFeed (dummy)]: {content}"


class MockAIProvider(BaseProvider, BaseAIProvider):
    """
    Mock AI Provider simulating advanced language model rewriting and summarization.
    """
    def __init__(self, config: Dict[str, Any] = None):
        BaseAIProvider.__init__(self, config)

    def validate_config(self) -> None:
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        return f"[Mock AI Summary]: Summary\n[Mock AI Rewrite]: {prompt}"

    def rewrite(self, title: str, content: str) -> str:
        summary = f"Summary of '{title}': This article discusses the key themes of {content[:60]}..."
        return f"[Mock AI Summary]: {summary}\n[Mock AI Rewrite]: Optimized version of: {content}"
