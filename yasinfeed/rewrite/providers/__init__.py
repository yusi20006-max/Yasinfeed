# yasinfeed/rewrite/providers package
from abc import ABC, abstractmethod
from yasinfeed.rewrite.providers.base import BaseAIProvider

class BaseProvider(ABC):
    """
    Abstract base class for all content rewrite and transformation providers (pipeline-level).
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
    def __init__(self, config: dict = None):
        pass

    def rewrite(self, title: str, content: str) -> str:
        return f"[Rewritten by YasinFeed (dummy)]: {content}"


class MockAIProvider(BaseAIProvider, BaseProvider):
    """
    Mock AI Provider simulating advanced language model rewriting and summarization.
    """
    def __init__(self, config: dict = None):
        BaseAIProvider.__init__(self, config)

    def validate_config(self) -> None:
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        # Extract title and content from prompt if structured
        # Otherwise, generic response
        return f"[Mock AI Summary]: Summary of prompt...\n[Mock AI Rewrite]: Optimized version"

    def rewrite(self, title: str, content: str) -> str:
        summary = f"Summary of '{title}': This article discusses the key themes of {content[:60]}..."
        return f"[Mock AI Summary]: {summary}\n[Mock AI Rewrite]: Optimized version of: {content}"
