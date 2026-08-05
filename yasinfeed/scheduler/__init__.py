from yasinfeed.engine import BaseModule
from yasinfeed.scheduler.scheduler import Scheduler, Job

class SchedulerModule(BaseModule):
    """
    Schedules and executes recurring tasks (fetch jobs, publishing queues).
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing scheduler module...")
        self.enabled = self.config.get("scheduler", {}).get("enabled", True)
        self.logger.info("Scheduler status: %s", "enabled" if self.enabled else "disabled")

        self.scheduler = Scheduler(logger=self.logger)
        return True

    def start(self) -> bool:
        self.logger.info("Scheduler module started. Periodic triggers set up.")
        if self.enabled:
            # Register default automated job
            fetch_interval = self.config.get("fetch", {}).get("interval_seconds", 300)
            self.scheduler.add_job(
                name="fetch_and_process",
                func=self.fetch_and_process,
                interval=fetch_interval,
                run_immediately=False
            )
            # Start scheduler thread
            self.scheduler.start()
        return True

    def stop(self) -> bool:
        self.logger.info("Scheduler module stopped. Active timers and threads cancelled.")
        self.scheduler.stop()
        return True

    def fetch_and_process(self) -> None:
        """
        The default end-to-end automation pipeline.
        Fetches feed items from the FetchModule, updates and saves articles
        using the StorageModule, rewrites them using the RewriteModule,
        and distributes/publishes the rewritten articles via the PublisherModule.
        """
        self.logger.info("Executing automated fetch_and_process pipeline...")

        # Access sibling modules via engine
        storage = self.engine.modules.get("storage")
        fetch = self.engine.modules.get("fetch")
        rewrite = self.engine.modules.get("rewrite")
        publisher = self.engine.modules.get("publisher")

        if not fetch:
            self.logger.warning("Fetch module is not available. Skipping automation loop.")
            return

        try:
            # 1. Fetch raw items
            raw_items = fetch.fetch_sources()
            if not raw_items:
                self.logger.info("No raw feed items fetched.")
                return

            self.logger.info("Fetched %d raw items.", len(raw_items))

            for item in raw_items:
                article_id = item.get("id")
                if not article_id:
                    self.logger.warning("Fetched item missing 'id' field, skipping: %s", item)
                    continue

                # 2. Check storage for existing article to avoid redundant processing
                existing_article = None
                if storage:
                    try:
                        existing_article = storage.get_article(article_id)
                    except Exception as ex:
                        self.logger.error("Error reading article %s from storage: %s", article_id, ex)

                # Skip if already completed
                if existing_article and existing_article.rewrite_status == "completed":
                    self.logger.debug("Article %s has already been processed and completed. Skipping.", article_id)
                    continue

                # 3. Form standard Article model
                from yasinfeed.models import Article
                from datetime import datetime, timezone

                # Parse published_at or default to now
                published_at = item.get("published_at") or datetime.now(timezone.utc)

                article = Article(
                    id=article_id,
                    source_id=item.get("source_id", "default-source"),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    original_url=item.get("url", ""),
                    published_at=published_at,
                    rewrite_status="pending",
                    published_outputs=[]
                )

                # Save raw article to storage if available
                if storage:
                    try:
                        storage.save_article(article)
                    except Exception as ex:
                        self.logger.error("Failed to save raw article %s to storage: %s", article_id, ex)

                # 4. Rewrite content
                rewritten_content = article.content
                if rewrite:
                    try:
                        rewritten_content = rewrite.rewrite_content(article.title, article.content)
                        article.rewritten_content = rewritten_content
                        article.rewrite_status = "completed"
                    except Exception as ex:
                        self.logger.error("Failed to rewrite article %s: %s", article_id, ex)
                        # We can skip or proceed with original content. Let's keep status pending/failed.
                        article.rewrite_status = "failed"

                # 5. Distribute / Publish
                published_outputs = []
                if publisher and article.rewrite_status == "completed":
                    try:
                        # Eitaa
                        if publisher.publish_to_eitaa(rewritten_content):
                            published_outputs.append("eitaa")
                    except Exception as ex:
                        self.logger.error("Failed publishing %s to Eitaa: %s", article_id, ex)

                    try:
                        # PWA
                        if publisher.publish_to_pwa({"title": article.title, "content": rewritten_content}):
                            published_outputs.append("pwa")
                    except Exception as ex:
                        self.logger.error("Failed publishing %s to PWA: %s", article_id, ex)

                    try:
                        # RSS
                        if publisher.publish_to_rss({"title": article.title, "content": rewritten_content}):
                            published_outputs.append("rss")
                    except Exception as ex:
                        self.logger.error("Failed publishing %s to RSS: %s", article_id, ex)

                article.published_outputs = published_outputs

                # 6. Save updated Article back to storage
                if storage:
                    try:
                        storage.save_article(article)
                    except Exception as ex:
                        self.logger.error("Failed to save processed article %s to storage: %s", article_id, ex)

            self.logger.info("Successfully completed automated fetch_and_process pipeline iteration.")

        except Exception as e:
            self.logger.error("Error running fetch_and_process pipeline: %s", e, exc_info=True)
