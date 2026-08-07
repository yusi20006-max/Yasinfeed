from typing import List, Dict
from datetime import datetime, timezone
import hashlib

from yasinfeed.engine import BaseModule
from yasinfeed.fetch.fetcher import FeedFetcher
from yasinfeed.retry import retry


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

        # Merge strategy from config
        self.content_merge_strategy = self.config.get(
            "fetch", {}
        ).get("content_merge_strategy", "priority")

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


    def _normalize_title(self, title: str) -> str:
        if not title:
            return ""
        return " ".join(title.lower().strip().split())


    def fetch_sources(self) -> List[Dict]:
        """
        Fetch all enabled feed sources and convert entries
        into standard pipeline items.
        """
        monitoring = self.engine.modules.get("monitoring")
        if monitoring:
            monitoring.metrics.inc("fetch_cycles")

        self.logger.info(
            "Fetching registered feed sources..."
        )

        storage = self.engine.modules.get("storage")

        if not storage:
            self.logger.error(
                "Storage module unavailable."
            )
            return []

        def _do_fetch():
            sources = storage.list_feed_sources()
            all_raw_items = []
            integration = self.engine.modules.get("integration")

            for source in sources:
                if not source.enabled:
                    continue

                # Update fetch count
                source.fetch_count = getattr(source, "fetch_count", 0) + 1
                source_success = False

                try:
                    self.logger.info(
                        "Fetching source: %s",
                        source.url
                    )

                    # Fetch with retry (exponential backoff)
                    feed = retry(
                        lambda: self.fetcher.fetch(source.url),
                        retries=3,
                        delay=1,
                        backoff=2
                    )

                    source_success = True
                    source.success_count = getattr(source, "success_count", 0) + 1
                    source.last_fetched_at = datetime.now(timezone.utc)
                    source.last_error = None

                    # Gather items from this source
                    for entry in feed.entries:
                        title = getattr(entry, "title", "")
                        content = getattr(entry, "description", "") or getattr(entry, "summary", "") or ""
                        url = getattr(entry, "link", "")

                        article_id = hashlib.sha256(
                            url.encode("utf-8")
                        ).hexdigest()[:16]

                        item_dict = {
                            "id": article_id,
                            "source_id": source.id,
                            "source_name": source.name,
                            "source_priority": getattr(source, "priority", 1),
                            "source_weight": getattr(source, "weight", 1.0),
                            "source_reliability_score": getattr(source, "reliability_score", 1.0),
                            "title": title,
                            "content": content,
                            "url": url,
                            "published_at": datetime.now(timezone.utc)
                        }
                        all_raw_items.append(item_dict)
                        if integration:
                            integration.trigger_event("on_article_fetched", item_dict)

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
                    source.failure_count = getattr(source, "failure_count", 0) + 1
                    source.last_error = str(e)
                    if monitoring:
                        monitoring.metrics.record_error("fetch", "SourceFetchError", f"{source.name}: {str(e)}")
                        monitoring.log_event(
                            event_type="source_fetch_failure",
                            severity="warning",
                            module="fetch",
                            message=f"Failed to fetch from {source.name}",
                            details={"url": source.url, "error": str(e)}
                        )

                # Update reliability score
                total_fetches = getattr(source, "fetch_count", 1)
                successes = getattr(source, "success_count", 0)
                source.reliability_score = successes / total_fetches if total_fetches > 0 else 0.0

                # Save updated source back to storage
                try:
                    storage.save_feed_source(source)
                except Exception as se:
                    self.logger.error("Failed to save updated source statistics: %s", se)

            # Perform cross-source duplicate detection & content merging
            merged_items = self._aggregate_and_merge_items(all_raw_items)
            return merged_items

        if monitoring:
            with monitoring.metrics.timing("fetch_sources"):
                return _do_fetch()
        else:
            return _do_fetch()


    def _aggregate_and_merge_items(self, items: List[Dict]) -> List[Dict]:
        """
        Groups items by duplicates (same URL/ID or normalized title)
        and merges them based on content_merge_strategy.
        """
        if not items:
            return []

        # Step 1: Identify duplicates and group them
        groups = []
        for item in items:
            item_id = item["id"]
            norm_title = self._normalize_title(item["title"])

            # Find if there is an existing group containing an item with the same ID or same normalized title
            found_group = None
            for g in groups:
                if any(x["id"] == item_id or (norm_title and self._normalize_title(x["title"]) == norm_title) for x in g):
                    found_group = g
                    break

            if found_group is not None:
                found_group.append(item)
            else:
                groups.append([item])

        results = []

        # Step 2: Merge each group
        for group in groups:
            # Sort group items by source rank (priority desc, weight desc, reliability desc)
            group.sort(
                key=lambda x: (
                    x.get("source_priority", 1),
                    x.get("source_weight", 1.0),
                    x.get("source_reliability_score", 1.0)
                ),
                reverse=True
            )

            primary_item = group[0]

            if len(group) == 1:
                # No duplicate, return as-is
                results.append(self._clean_item_metadata(primary_item))
                continue

            self.logger.info(
                "Duplicate detected across %d sources for title: %s",
                len(group),
                primary_item["title"]
            )

            if self.content_merge_strategy == "combine":
                # Combine content across all duplicate sources
                merged_content = primary_item["content"] or ""
                seen_contents = {merged_content.strip()}

                for extra_item in group[1:]:
                    extra_content = extra_item["content"] or ""
                    if extra_content.strip() and extra_content.strip() not in seen_contents:
                        merged_content += f"\n\n--- [Alternative Content from {extra_item['source_name']}] ---\n{extra_content}"
                        seen_contents.add(extra_content.strip())

                primary_item["content"] = merged_content

            # clean up raw/source-specific keys for final return
            results.append(self._clean_item_metadata(primary_item))

        return results


    def _clean_item_metadata(self, item: Dict) -> Dict:
        """Removes helper keys used for prioritization/merging and returns standard dictionary."""
        return {
            "id": item["id"],
            "source_id": item["source_id"],
            "title": item["title"],
            "content": item["content"],
            "url": item["url"],
            "published_at": item["published_at"]
        }


    def stop(self) -> bool:

        self.logger.info(
            "Fetch module stopped."
        )

        return True
