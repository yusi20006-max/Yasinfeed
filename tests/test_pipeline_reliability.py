import unittest
from datetime import datetime, timezone
from yasinfeed.models.article import Article
from yasinfeed.rewrite.stages import BaseStage, SanitizationStage, RewriteStage
from yasinfeed.rewrite.pipeline_providers import DummyProvider
from yasinfeed.rewrite.pipeline import ContentPipeline

class MockFailureStage(BaseStage):
    """A stage designed to raise an exception for testing reliability."""
    def __init__(self, critical: bool = True):
        super().__init__(critical=critical)

    def process(self, article: Article) -> Article:
        raise ValueError("Simulated stage error")

    def fallback(self, article: Article, exception: Exception) -> Article:
        article.title = f"Fallback: {article.title}"
        return article


class TestPipelineReliability(unittest.TestCase):
    def setUp(self):
        self.article = Article(
            id="art-rel-1",
            source_id="src-1",
            title="Sample Title",
            content="Sample Content",
            original_url="https://example.com",
            published_at=datetime.now(timezone.utc)
        )

    def test_critical_stage_failure(self):
        # A critical failure should stop the pipeline, raise the error, and set rewrite_status to failed
        pipeline = ContentPipeline([
            SanitizationStage(),
            MockFailureStage(critical=True)
        ])

        with self.assertRaises(ValueError) as ctx:
            pipeline.process(self.article)

        self.assertEqual(str(ctx.exception), "Simulated stage error")
        self.assertEqual(self.article.rewrite_status, "failed")

        # Metadata should record the failure details
        run_meta = self.article.pipeline_metadata.get("pipeline_run", {})
        self.assertIn("SanitizationStage", run_meta.get("stages_executed", []))
        self.assertIn("MockFailureStage", run_meta.get("stages_executed", []))
        self.assertEqual(len(run_meta.get("failures", [])), 1)
        self.assertTrue(run_meta["failures"][0]["critical"])

    def test_non_critical_stage_failure_recovery(self):
        # A non-critical failure should be bypassed and the fallback method should execute
        pipeline = ContentPipeline([
            SanitizationStage(),
            MockFailureStage(critical=False),
            RewriteStage(DummyProvider())
        ])

        processed = pipeline.process(self.article)

        # Rewrite status should succeed because MockFailureStage is non-critical and RewriteStage runs after it
        self.assertEqual(processed.rewrite_status, "completed")
        self.assertEqual(processed.title, "Fallback: Sample Title")

        # Metadata should have captured both success and the bypassed failure
        run_meta = processed.pipeline_metadata.get("pipeline_run", {})
        self.assertEqual(len(run_meta.get("stages_executed", [])), 3)
        self.assertEqual(len(run_meta.get("failures", [])), 1)
        self.assertFalse(run_meta["failures"][0]["critical"])
        self.assertEqual(run_meta["failures"][0]["stage"], "MockFailureStage")

if __name__ == "__main__":
    unittest.main()
