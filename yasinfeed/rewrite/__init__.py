from yasinfeed.rewrite.providers.base import BaseProvider
from yasinfeed.engine import BaseModule
from yasinfeed.models import Article
from yasinfeed.rewrite.providers.factory import create_provider
from yasinfeed.rewrite.providers.base import AIProviderError, AIConfigurationError


class AIProviderAdapter(BaseProvider):
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider

    def rewrite(self, title: str, content: str) -> str:
        if hasattr(self.ai_provider, "rewrite"):
            return self.ai_provider.rewrite(title, content)
        prompt = f"Title: {title}\nContent: {content}"
        return self.ai_provider.generate(prompt)


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

        from yasinfeed.rewrite.pipeline import ContentPipeline
        from yasinfeed.rewrite.stages import (
            SanitizationStage,
            RewriteStage,
            TranslationStage,
            ContentAnalysisStage,
            MetadataTaggingStage
        )

        # ContentAnalysisStage is configuration-driven and optional
        intelligence_config = self.config.get("rewrite", {}).get("intelligence", {})
        intelligence_enabled = intelligence_config.get("enabled", True)

        self.pipeline = ContentPipeline([
            SanitizationStage(),
            RewriteStage(self.provider),
            TranslationStage(target_lang="en"),
            ContentAnalysisStage(enabled=intelligence_enabled),
            MetadataTaggingStage()
        ], engine=self.engine)

        return True

    def start(self) -> bool:
        self.logger.info("Rewrite module started.")
        return True

    def process_article(self, article: Article) -> Article:
        """
        Runs the full modular ContentPipeline workflow on an Article.
        """
        self.logger.info("Processing article through Content Pipeline: %s", article.id)
        return self.pipeline.process(article)

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
