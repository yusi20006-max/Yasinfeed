from yasinfeed.engine import BaseModule
from yasinfeed.rewrite.providers.factory import create_provider
from yasinfeed.rewrite.providers.base import AIProviderError, AIConfigurationError


class RewriteModule(BaseModule):
    """
    Handles rewriting and summary generation for news content.
    Provides standard interface to be utilized by agent/scheduler pipelines.
    Supports modular AI Providers (Dummy, OpenAI, Hugging Face).
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing rewrite module...")

        rewrite_config = self.config.get("rewrite", {})
        self.provider_name = rewrite_config.get("provider", "dummy")
        self.logger.info("Content rewrite provider configured: %s", self.provider_name)

        # Extract specific config block for the provider
        provider_config = rewrite_config.get(self.provider_name, {})

        try:
            self.provider = create_provider(self.provider_name, provider_config)
            self.logger.info("Content rewrite provider instantiated successfully: %s", self.provider_name)
        except AIConfigurationError as e:
            self.logger.error("Configuration error in rewrite provider %s: %s", self.provider_name, e)
            return False
        except Exception as e:
            self.logger.error("Failed to initialize rewrite provider %s: %s", self.provider_name, e, exc_info=True)
            return False

        return True

    def start(self) -> bool:
        self.logger.info("Rewrite module started.")
        return True

    def rewrite_content(self, title: str, content: str) -> str:
        """
        Rewrites content using the configured AI provider.
        If generation fails, falls back gracefully to a warning and original content.
        """
        self.logger.info("Rewriting content for title: %s", title)
        prompt = f"Title: {title}\nContent: {content}"

        try:
            return self.provider.generate(prompt)
        except AIProviderError as e:
            self.logger.warning("AI Generation failed for title '%s': %s. Falling back to original content.", title, e)
            return f"[Rewritten Failed - Fallback]: {content}"
        except Exception as e:
            self.logger.error("Unexpected error in rewrite_content for title '%s': %s", title, e, exc_info=True)
            return f"[Rewritten Failed - Fallback]: {content}"

    def stop(self) -> bool:
        self.logger.info("Rewrite module stopped.")
        return True
