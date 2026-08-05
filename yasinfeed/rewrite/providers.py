from abc import ABC, abstractmethod

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


class MockAIProvider(BaseProvider):
    """
    Mock AI Provider simulating advanced language model rewriting and summarization.
    """
    def rewrite(self, title: str, content: str) -> str:
        summary = f"Summary of '{title}': This article discusses the key themes of {content[:60]}..."
        return f"[Mock AI Summary]: {summary}\n[Mock AI Rewrite]: Optimized version of: {content}"
