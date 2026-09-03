import unittest
from datetime import datetime, timezone
from yasinfeed.models import Article
from yasinfeed.rewrite.pipeline_providers import DummyProvider, MockAIProvider
from yasinfeed.rewrite.stages import SanitizationStage, RewriteStage, TranslationStage, MetadataTaggingStage
from yasinfeed.rewrite.pipeline import ContentPipeline
from yasinfeed.rewrite import RewriteModule
from yasinfeed.engine import YasinFeedEngine

class TestContentPipeline(unittest.TestCase):
    def setUp(self):
        # Sample Article for testing
        self.article = Article(
            id="test-art-1",
            source_id="test-src-1",
            title="<p>Breaking News:  Artificial Intelligence and Python  </p>",
            content="<div>An exciting AI LLM release was announced today.\n\n It's software built with python!</div>",
            original_url="https://example.com/test",
            published_at=datetime.now(timezone.utc),
            rewrite_status="pending"
        )

    def test_sanitization_stage(self):
        stage = SanitizationStage()
        cleaned_art = stage.process(self.article)
        self.assertEqual(cleaned_art.title, "Breaking News: Artificial Intelligence and Python")
        # Check standard duplicate spacing/newline removal
        self.assertNotIn("<div>", cleaned_art.content)
        self.assertNotIn("</div>", cleaned_art.content)
        self.assertIn("An exciting AI LLM release", cleaned_art.content)

    def test_rewrite_stage_dummy(self):
        provider = DummyProvider()
        stage = RewriteStage(provider)
        # First sanitize to ensure uniform input
        SanitizationStage().process(self.article)
        processed = stage.process(self.article)
        self.assertEqual(processed.rewrite_status, "completed")
        self.assertIn("[Rewritten by YasinFeed (dummy)]", processed.rewritten_content)

    def test_rewrite_stage_mock_ai(self):
        provider = MockAIProvider()
        stage = RewriteStage(provider)
        SanitizationStage().process(self.article)
        processed = stage.process(self.article)
        self.assertEqual(processed.rewrite_status, "completed")
        self.assertIn("[Mock AI Summary]", processed.rewritten_content)
        self.assertIn("[Mock AI Rewrite]", processed.rewritten_content)

    def test_translation_stage(self):
        # Setup initial rewritten content
        self.article.rewritten_content = "Optimized text here"
        stage = TranslationStage(target_lang="fa")
        processed = stage.process(self.article)
        self.assertIn("[Translated to FA]", processed.rewritten_content)

    def test_metadata_tagging_stage(self):
        self.article.title = "AI announcement"
        self.article.content = "New release of machine learning python software package"
        self.article.rewritten_content = "Some summary"

        stage = MetadataTaggingStage()
        processed = stage.process(self.article)
        self.assertIn("#ai", processed.rewritten_content)
        self.assertIn("#news", processed.rewritten_content)
        self.assertIn("#tech", processed.rewritten_content)

    def test_content_pipeline_full_run(self):
        # Test full sequential execution
        provider = MockAIProvider()
        pipeline = ContentPipeline([
            SanitizationStage(),
            RewriteStage(provider),
            TranslationStage(target_lang="en"),
            MetadataTaggingStage()
        ])

        result = pipeline.process(self.article)

        # HTML tag should be stripped
        self.assertNotIn("<p>", result.title)
        # Rewrite status should be completed
        self.assertEqual(result.rewrite_status, "completed")
        # Translation tag should be added
        self.assertIn("[Translated to EN]", result.rewritten_content)
        # Keywords should trigger hashtags (#ai, #tech, #news)
        self.assertIn("#ai", result.rewritten_content)
        self.assertIn("#tech", result.rewritten_content)
        self.assertIn("#news", result.rewritten_content)

    def test_rewrite_module_integration(self):
        # Create an engine to test module initialization and integration
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        # Let's customize config to use mock_ai provider
        engine.initialize()
        rewrite_mod = engine.modules["rewrite"]

        # Overwrite config for rewrite provider and re-initialize
        rewrite_mod.config["rewrite"] = {"provider": "mock_ai"}
        rewrite_mod.initialize()

        self.assertEqual(rewrite_mod.provider_name, "mock_ai")
        self.assertIsInstance(rewrite_mod.provider, MockAIProvider)

        # Process article through module
        processed = rewrite_mod.process_article(self.article)
        self.assertEqual(processed.rewrite_status, "completed")
        self.assertIn("[Translated to EN]", processed.rewritten_content)
        self.assertIn("#ai", processed.rewritten_content)

if __name__ == "__main__":
    unittest.main()
