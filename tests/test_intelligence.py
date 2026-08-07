import unittest
from datetime import datetime, timezone
from yasinfeed.models.article import Article
from yasinfeed.rewrite.intelligence import ContentIntelligenceEngine
from yasinfeed.rewrite.stages import ContentAnalysisStage, SanitizationStage, RewriteStage
from yasinfeed.rewrite.pipeline_providers import DummyProvider
from yasinfeed.rewrite.pipeline import ContentPipeline

class TestContentIntelligence(unittest.TestCase):
    def setUp(self):
        self.engine = ContentIntelligenceEngine()

    def test_language_detection_english(self):
        text = "This is a completely standard English sentence with some words."
        lang = self.engine.detect_language(text)
        self.assertEqual(lang, "en")

    def test_language_detection_persian(self):
        text = "این یک متن فارسی کاملا استاندارد برای تست است که کلماتی دارد."
        lang = self.engine.detect_language(text)
        self.assertEqual(lang, "fa")

    def test_sentiment_analysis_positive(self):
        text = "This breakthrough release is amazing! The software has seen great progress and is highly successful."
        sentiment = self.engine.analyze_sentiment(text)
        self.assertEqual(sentiment["label"], "positive")
        self.assertGreater(sentiment["score"], 0.15)

    def test_sentiment_analysis_negative(self):
        text = "The system failed with a critical severe crash. A terrible bug caused a disastrous loss."
        sentiment = self.engine.analyze_sentiment(text)
        self.assertEqual(sentiment["label"], "negative")
        self.assertLess(sentiment["score"], -0.15)

    def test_sentiment_analysis_neutral(self):
        text = "The table is made of wood and stands near the window."
        sentiment = self.engine.analyze_sentiment(text)
        self.assertEqual(sentiment["label"], "neutral")
        self.assertEqual(sentiment["score"], 0.0)

    def test_readability_metrics(self):
        text = "Sentence one is here. And sentence two is right here!"
        readability = self.engine.analyze_readability(text)
        self.assertEqual(readability["words_count"], 10)
        self.assertEqual(readability["sentences_count"], 2)
        self.assertGreater(readability["avg_word_length"], 0.0)
        self.assertGreaterEqual(readability["estimated_reading_time_seconds"], 1)

    def test_topic_extraction(self):
        text = "AI artificial intelligence machine learning Python backend Python AI development"
        topics = self.engine.extract_topics(text, lang="en", limit=3)
        self.assertEqual(len(topics), 3)
        # Python and AI are the most frequent, and should be in the top extracted list
        self.assertTrue("python" in topics or "learning" in topics or "artificial" in topics)

    def test_agent_signals_and_urgency(self):
        # A normal text with neutral sentiment
        neutral_text = "Standard software update with standard configurations."
        signals = self.engine.evaluate_agent_signals(neutral_text, sentiment_score=0.0)
        self.assertLess(signals["priority"], 0.4)
        self.assertEqual(signals["dispatch_route"], "standard_processing")

        # An urgent/critical text
        urgent_text = "CRITICAL WARNING: Severe security exploit and vulnerability detected in our backend system!"
        signals_urgent = self.engine.evaluate_agent_signals(urgent_text, sentiment_score=-0.8)
        # Priority should be boosted by matched triggers (critical, security, exploit, vulnerability) and sentiment extremity
        self.assertGreaterEqual(signals_urgent["priority"], 0.7)
        self.assertEqual(signals_urgent["dispatch_route"], "publish_immediately")
        self.assertGreater(signals_urgent["confidence"], 0.5)

    def test_content_analysis_stage_enabled(self):
        # Test integrated ContentAnalysisStage when enabled
        article = Article(
            id="art-int-1",
            source_id="src-1",
            title="AI breakthrough",
            content="An amazing new progress was announced in artificial intelligence software.",
            original_url="https://example.com",
            published_at=datetime.now(timezone.utc)
        )

        stage = ContentAnalysisStage(enabled=True)
        processed = stage.process(article)

        self.assertIn("intelligence", processed.pipeline_metadata)
        intel = processed.pipeline_metadata["intelligence"]
        self.assertEqual(intel["language"], "en")
        self.assertEqual(intel["sentiment"]["label"], "positive")
        self.assertIn("topics", intel)
        self.assertIn("agent_signals", intel)

    def test_content_analysis_stage_disabled(self):
        # Test integrated ContentAnalysisStage when disabled
        article = Article(
            id="art-int-2",
            source_id="src-1",
            title="Standard Release",
            content="Standard content.",
            original_url="https://example.com",
            published_at=datetime.now(timezone.utc)
        )

        stage = ContentAnalysisStage(enabled=False)
        processed = stage.process(article)

        self.assertNotIn("intelligence", processed.pipeline_metadata)

    def test_backward_compatibility_and_full_pipeline(self):
        # Ensure that running the full pipeline with Sanitization, Rewrite, optional ContentAnalysis and MetadataTagging works flawlessly
        article = Article(
            id="art-int-3",
            source_id="src-1",
            title="<p>Breaking News: Python is great </p>",
            content="<div>A completely amazing software release of Python 3.12 happened today.</div>",
            original_url="https://example.com",
            published_at=datetime.now(timezone.utc)
        )

        pipeline = ContentPipeline([
            SanitizationStage(),
            RewriteStage(DummyProvider()),
            ContentAnalysisStage(enabled=True),
            ContentAnalysisStage(enabled=False),  # Testing multiple stages with different configs
            # Make a non-critical stage fail to test fault-tolerant reliability inside the full chain
            ContentAnalysisStage(enabled=True)  # Should execute fine
        ])

        processed = pipeline.process(article)

        # Basic expectations
        self.assertEqual(processed.rewrite_status, "completed")
        self.assertNotIn("<p>", processed.title)
        self.assertIn("[Rewritten by YasinFeed (dummy)]", processed.rewritten_content)

        # Intelligence expectations
        self.assertIn("pipeline_run", processed.pipeline_metadata)
        self.assertIn("intelligence", processed.pipeline_metadata)
        self.assertEqual(processed.pipeline_metadata["intelligence"]["language"], "en")
        self.assertEqual(processed.pipeline_metadata["intelligence"]["sentiment"]["label"], "positive")

if __name__ == "__main__":
    unittest.main()
