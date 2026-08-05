from yasinfeed.engine import BaseModule
from yasinfeed.models import Article
from yasinfeed.rewrite.providers import DummyProvider, MockAIProvider
from yasinfeed.rewrite.stages import SanitizationStage, RewriteStage, TranslationStage, MetadataTaggingStage
from yasinfeed.rewrite.pipeline import ContentPipeline

class RewriteModule(BaseModule):
    """
    Handles rewriting and summary generation for news content.
    Provides standard interface to be utilized by agent/scheduler pipelines.
    Now leverages ContentPipeline and modular processing stages.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing rewrite module...")
        self.provider_name = self.config.get("rewrite", {}).get("provider", "dummy")
        self.logger.info("Content rewrite provider loaded: %s", self.provider_name)

        # Initialize the selected provider
        if self.provider_name == "mock_ai":
            self.provider = MockAIProvider()
        else:
            self.provider = DummyProvider()

        # Initialize default pipeline and register standard stages
        self.pipeline = ContentPipeline()
        self.pipeline.add_stage(SanitizationStage())
        self.pipeline.add_stage(RewriteStage(self.provider))
        self.pipeline.add_stage(TranslationStage())
        self.pipeline.add_stage(MetadataTaggingStage())

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
        Legacy/backward compatible placeholder rewrite method.
        Delegates directly to the active provider.
        """
        self.logger.info("Rewriting content for title: %s", title)
        return self.provider.rewrite(title, content)

    def stop(self) -> bool:
        self.logger.info("Rewrite module stopped.")
        return True
