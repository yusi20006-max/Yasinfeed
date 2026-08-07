from typing import List, Dict
from datetime import datetime, timezone
import hashlib

from yasinfeed.engine import BaseModule
from yasinfeed.fetch.fetcher import FeedFetcher


class FetchModule(BaseModule):
    """
    Responsible for fetching content sources.
    Loads and processes RSS inputs and other web streams.
    """

    def initialize(self) -> bool:
        self.logger.info("Initializing fetch module...")

        self.interval = self.config.get(
            "fetch", {}
        ).get("interval_seconds", 300)

        self.fetcher = FeedFetcher()

        self.logger.info(
            "Fetch interval set to %d seconds.",
            self.interval
        )

        return True


    def start(self) -> bool:
        self.logger.info(
            "Fetch module started. Monitoring configured content sources."
        )

        return True


    def fetch_sources(self) -> List[Dict]:
        """
        Fetch all enabled feed sources and convert entries
        into standard pipeline items.
        """

        self.logger.info(
            "Fetching registered feed sources..."
        )

        results = []

        storage = self.engine.modules.get("storage")

        if not storage:
            self.logger.error(
                "Storage module unavailable."
            )
            return results


        sources = storage.list_feed_sources()

        for source in sources:

            if not source.enabled:
                continue

            try:
                self.logger.info(
                    "Fetching source: %s",
                    source.url
                )

                feed = self.fetcher.fetch(
                    source.url
                )


                for entry in feed.entries:

                    title = getattr(
                        entry,
                        "title",
                        ""
                    )

                    content = getattr(
                        entry,
                        "description",
                        ""
                    )


                    url = getattr(
                        entry,
                        "link",
                        ""
                    )


                    article_id = hashlib.sha256(
                        url.encode("utf-8")
                    ).hexdigest()[:16]


                    results.append(
                        {
                            "id": article_id,
                            "source_id": source.id,
                            "title": title,
                            "content": content,
                            "url": url,
                            "published_at": datetime.now(
                                timezone.utc
                            )
                        }
                    )


                monitoring = self.engine.modules.get("monitoring")
                if monitoring:
                    monitoring.metrics.inc("articles_fetched", len(feed.entries))

                self.logger.info(
                    "Fetched %d items from %s",
                    len(feed.entries),
                    source.name
                )


            except Exception as e:

                self.logger.error(
                    "Failed fetching %s: %s",
                    source.url,
                    e,
                    exc_info=True
                )


        return results


    def stop(self) -> bool:

        self.logger.info(
            "Fetch module stopped."
        )

        return True
