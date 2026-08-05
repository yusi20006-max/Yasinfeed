import unittest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from yasinfeed.scheduler.scheduler import Scheduler, Job
from yasinfeed.scheduler import SchedulerModule
from yasinfeed.engine import YasinFeedEngine
from yasinfeed.models import Article

class TestScheduler(unittest.TestCase):
    """
    Unit and integration tests for the Scheduler and Automation Layer.
    """

    def setUp(self):
        self.scheduler = Scheduler()

    def tearDown(self):
        self.scheduler.stop()

    def test_job_registration_success(self):
        """Test registering a valid periodic job."""
        runs = []
        def job_func():
            runs.append(True)

        job = self.scheduler.add_job("test_job", job_func, 10.0, run_immediately=False)

        self.assertEqual(job.name, "test_job")
        self.assertEqual(job.interval, 10.0)
        self.assertTrue(job.enabled)
        self.assertEqual(job.run_count, 0)
        self.assertEqual(job.last_status, "pending")
        self.assertIsNone(job.last_run_start)

        # Check next_run is approx 10 seconds from now
        now = datetime.now(timezone.utc)
        self.assertIsNotNone(job.next_run)
        self.assertTrue(now + timedelta(seconds=9) <= job.next_run <= now + timedelta(seconds=11))

        # Retrieve job
        retrieved_job = self.scheduler.get_job("test_job")
        self.assertEqual(retrieved_job, job)

        # List jobs
        jobs = self.scheduler.list_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0], job)

    def test_job_registration_duplicate_name(self):
        """Test registering a job with a name that already exists raises ValueError."""
        def dummy():
            pass
        self.scheduler.add_job("dummy_job", dummy, 5.0)
        with self.assertRaises(ValueError):
            self.scheduler.add_job("dummy_job", dummy, 5.0)

    def test_job_registration_invalid_interval(self):
        """Test registering a job with zero or negative interval raises ValueError."""
        def dummy():
            pass
        with self.assertRaises(ValueError):
            self.scheduler.add_job("dummy_job", dummy, 0)
        with self.assertRaises(ValueError):
            self.scheduler.add_job("dummy_job", dummy, -1.5)

    def test_job_removal(self):
        """Test removing a registered job."""
        def dummy():
            pass
        self.scheduler.add_job("removable", dummy, 1.0)
        self.assertIsNotNone(self.scheduler.get_job("removable"))

        self.scheduler.remove_job("removable")
        self.assertIsNone(self.scheduler.get_job("removable"))

        with self.assertRaises(KeyError):
            self.scheduler.remove_job("non_existent")

    def test_job_pause_and_resume(self):
        """Test pausing and resuming a registered job."""
        def dummy():
            pass
        job = self.scheduler.add_job("pausable", dummy, 5.0)
        self.assertTrue(job.enabled)

        self.scheduler.pause_job("pausable")
        self.assertFalse(job.enabled)

        self.scheduler.resume_job("pausable")
        self.assertTrue(job.enabled)

        with self.assertRaises(KeyError):
            self.scheduler.pause_job("non_existent")
        with self.assertRaises(KeyError):
            self.scheduler.resume_job("non_existent")

    def test_job_execution_and_tracking_success(self):
        """Test executing a job successfully tracks counters, duration, status, and timestamps."""
        runs = []
        def job_func():
            time.sleep(0.05)
            runs.append(True)

        # Use very small interval and run immediately
        job = self.scheduler.add_job("quick_job", job_func, 0.1, run_immediately=True)
        self.scheduler.start()

        # Wait for the background execution
        time.sleep(0.2)
        self.scheduler.stop()

        self.assertGreaterEqual(job.run_count, 1)
        self.assertGreaterEqual(job.success_count, 1)
        self.assertEqual(job.failure_count, 0)
        self.assertEqual(job.last_status, "success")
        self.assertIsNotNone(job.last_run_start)
        self.assertIsNotNone(job.last_run_end)
        self.assertIsNotNone(job.last_duration)
        self.assertGreaterEqual(job.last_duration, 0.04)
        self.assertIsNone(job.last_error)

        # Verify dict representation contains serializable stats
        d = job.to_dict()
        self.assertEqual(d["name"], "quick_job")
        self.assertEqual(d["last_status"], "success")
        self.assertIsNotNone(d["last_run_start"])
        self.assertIsNotNone(d["last_run_end"])

    def test_job_execution_and_tracking_failure(self):
        """Test executing a job that fails tracks error messages and failures correctly."""
        def bad_func():
            raise RuntimeError("Something went wrong inside the job!")

        job = self.scheduler.add_job("failing_job", bad_func, 0.1, run_immediately=True)
        self.scheduler.start()

        time.sleep(0.2)
        self.scheduler.stop()

        self.assertGreaterEqual(job.run_count, 1)
        self.assertEqual(job.success_count, 0)
        self.assertGreaterEqual(job.failure_count, 1)
        self.assertEqual(job.last_status, "failed")
        self.assertIsNotNone(job.last_run_start)
        self.assertIsNotNone(job.last_run_end)
        self.assertIn("RuntimeError", job.last_error)
        self.assertIn("Something went wrong", job.last_error)

    def test_scheduler_module_lifecycle(self):
        """Test standard SchedulerModule lifecycle methods start/stop."""
        engine = YasinFeedEngine(config_path="/nonexistent.yaml")
        # Initialize config manually to ensure scheduler enabled
        engine.config = {
            "scheduler": {"enabled": True},
            "fetch": {"interval_seconds": 60}
        }

        module = SchedulerModule(engine)
        self.assertTrue(module.initialize())
        self.assertIsNotNone(module.scheduler)
        self.assertTrue(module.enabled)

        self.assertTrue(module.start())
        self.assertTrue(module.scheduler._running)

        # Verify default pipeline job registered
        default_job = module.scheduler.get_job("fetch_and_process")
        self.assertIsNotNone(default_job)
        self.assertEqual(default_job.interval, 60.0)

        self.assertTrue(module.stop())
        self.assertFalse(module.scheduler._running)

    def test_fetch_and_process_automation_pipeline(self):
        """Test that the default fetch_and_process pipeline runs end-to-end successfully."""
        engine = YasinFeedEngine(config_path="/nonexistent.yaml")
        engine.config = {
            "scheduler": {"enabled": True},
            "fetch": {"interval_seconds": 60}
        }

        # Create mocks for other modules
        mock_storage = MagicMock()
        mock_fetch = MagicMock()
        mock_rewrite = MagicMock()
        mock_publisher = MagicMock()

        # Wire up mock storage
        # get_article returns None so we treat the article as new
        mock_storage.get_article.return_value = None

        # Wire up mock fetch returning 1 item
        mock_fetch.fetch_sources.return_value = [
            {
                "id": "test-article-1",
                "source_id": "test-src",
                "title": "Unittest Title",
                "content": "Raw article content text.",
                "url": "https://example.com/test"
            }
        ]

        # Wire up mock rewrite
        mock_rewrite.rewrite_content.return_value = "Rewritten Content!"

        # Wire up mock publisher
        mock_publisher.publish_to_eitaa.return_value = True
        mock_publisher.publish_to_pwa.return_value = True
        mock_publisher.publish_to_rss.return_value = True

        engine.modules = {
            "storage": mock_storage,
            "fetch": mock_fetch,
            "rewrite": mock_rewrite,
            "publisher": mock_publisher
        }

        module = SchedulerModule(engine)
        self.assertTrue(module.initialize())

        # Trigger fetch_and_process manually to inspect behavior synchronously
        module.fetch_and_process()

        # Assertions
        # 1. We called fetch_sources()
        mock_fetch.fetch_sources.assert_called_once()

        # 2. Checked if article exists in storage
        mock_storage.get_article.assert_called_with("test-article-1")

        # 3. Saved raw article (first save) and updated/completed article (second save)
        self.assertEqual(mock_storage.save_article.call_count, 2)
        saved_article_calls = mock_storage.save_article.call_args_list

        # Examine final saved Article object
        final_article = saved_article_calls[-1][0][0]
        self.assertTrue(isinstance(final_article, Article))
        self.assertEqual(final_article.id, "test-article-1")
        self.assertEqual(final_article.rewritten_content, "Rewritten Content!")
        self.assertEqual(final_article.rewrite_status, "completed")
        self.assertEqual(final_article.published_outputs, ["eitaa", "pwa", "rss"])

        # 4. Rewrite content was called with correct args
        mock_rewrite.rewrite_content.assert_called_once_with("Unittest Title", "Raw article content text.")

        # 5. Publisher endpoints called with correct rewritten text
        mock_publisher.publish_to_eitaa.assert_called_once_with("Rewritten Content!")
        mock_publisher.publish_to_pwa.assert_called_once_with({"title": "Unittest Title", "content": "Rewritten Content!"})
        mock_publisher.publish_to_rss.assert_called_once_with({"title": "Unittest Title", "content": "Rewritten Content!"})

    def test_fetch_and_process_skip_completed_article(self):
        """Test that already completed articles are skipped during automated pipeline."""
        engine = YasinFeedEngine(config_path="/nonexistent.yaml")

        mock_storage = MagicMock()
        mock_fetch = MagicMock()
        mock_rewrite = MagicMock()
        mock_publisher = MagicMock()

        # Wire up mock storage to return an already completed article
        completed_article = Article(
            id="completed-1",
            source_id="src",
            title="Title",
            content="Content",
            original_url="http://",
            published_at=datetime.now(timezone.utc),
            rewritten_content="Already rewritten",
            rewrite_status="completed",
            published_outputs=["eitaa"]
        )
        mock_storage.get_article.return_value = completed_article

        mock_fetch.fetch_sources.return_value = [
            {
                "id": "completed-1",
                "title": "Title",
                "content": "Content",
                "url": "http://"
            }
        ]

        engine.modules = {
            "storage": mock_storage,
            "fetch": mock_fetch,
            "rewrite": mock_rewrite,
            "publisher": mock_publisher
        }

        module = SchedulerModule(engine)
        self.assertTrue(module.initialize())
        module.fetch_and_process()

        # Verify we skipped rewrite and publish
        mock_rewrite.rewrite_content.assert_not_called()
        mock_publisher.publish_to_eitaa.assert_not_called()
        # Storage.save_article shouldn't be called to rewrite/re-save
        mock_storage.save_article.assert_not_called()


if __name__ == "__main__":
    unittest.main()
