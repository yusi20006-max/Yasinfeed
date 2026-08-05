from yasinfeed.rewrite.providers.base import BaseProvider, BaseAIProvider, AIProviderError, AIConfigurationError, AICallError


class DummyProvider(BaseProvider):
    """
    Legacy Dummy provider mimicking existing simple placeholder rewrite logic.
    """
    def rewrite(self, title: str, content: str) -> str:
        return f"[Rewritten by YasinFeed (dummy)]: {content}"


class MockAIProvider(BaseAIProvider):
    """
    Mock AI Provider simulating advanced language model rewriting and summarization.
    """
    def validate_config(self) -> None:
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        # Fallback generate in case it's used directly
        return f"[Mock AI Rewrite]: Optimized version of: {prompt}"

    def rewrite(self, title: str, content: str) -> str:
        summary = f"Summary of '{title}': This article discusses the key themes of {content[:60]}..."
        return f"[Mock AI Summary]: {summary}\n[Mock AI Rewrite]: Optimized version of: {content}"
