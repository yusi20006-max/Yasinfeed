"""Publishing coordination for YasinFeed output channels."""

from __future__ import annotations

from typing import Any, Iterable

from yasinfeed.engine import BaseModule
from yasinfeed.publisher.eitaa import EitaaPublisher
from yasinfeed.publisher.pwa import PWAPublisher
from yasinfeed.publisher.rss import RSSPublisher


class PublisherModule(BaseModule):
    """Coordinate independent Eitaa, PWA JSON, and RSS publishing."""

    def initialize(self) -> bool:
        self.logger.info("Initializing publisher module...")
        pub_config = self.config.get("publisher", {})

        eitaa_config = pub_config.get("eitaa", {})
        pwa_config = pub_config.get("pwa", {})
        rss_config = pub_config.get("rss", {})

        self.eitaa_enabled = bool(eitaa_config.get("enabled", False))
        self.pwa_enabled = bool(pwa_config.get("enabled", False))
        self.rss_enabled = bool(rss_config.get("enabled", False))

        self.eitaa = None
        self.pwa = None
        self.rss = None

        if self.eitaa_enabled:
            token = eitaa_config.get("token")
            channel = eitaa_config.get("channel")
            if token and channel:
                self.eitaa = EitaaPublisher(token, channel)
                self.logger.info("Eitaa publisher initialized.")
            else:
                self.logger.warning("Eitaa enabled but token/channel missing.")
                self.eitaa_enabled = False

        if self.pwa_enabled:
            self.pwa = PWAPublisher(
                pwa_config.get("output_path", "data/pwa/feed.json"),
                base_url=pwa_config.get("base_url", ""),
            )
            self.logger.info("PWA JSON publisher initialized: %s", self.pwa.output_path)

        if self.rss_enabled:
            self.rss = RSSPublisher(
                rss_config.get("output_path", "data/rss/feed.xml"),
                title=rss_config.get("title", "YasinFeed"),
                link=rss_config.get("link", "http://127.0.0.1:8000/api/feed"),
                description=rss_config.get("description", "YasinFeed published news"),
            )
            self.logger.info("RSS publisher initialized: %s", self.rss.output_path)

        self.logger.info(
            "Publisher Channels - Eitaa: %s, PWA: %s, RSS: %s",
            self.eitaa_enabled,
            self.pwa_enabled,
            self.rss_enabled,
        )
        return True

    def start(self) -> bool:
        self.logger.info("Publisher module started.")
        return True

    @staticmethod
    def _articles(feed_data: Any) -> list[Any]:
        if feed_data is None:
            return []
        if isinstance(feed_data, dict):
            for key in ("articles", "items", "data"):
                value = feed_data.get(key)
                if isinstance(value, (list, tuple)):
                    return list(value)
            article = feed_data.get("article")
            return [article] if article is not None else []
        if isinstance(feed_data, (list, tuple)):
            return list(feed_data)
        return list(feed_data) if isinstance(feed_data, Iterable) and not isinstance(feed_data, (str, bytes)) else [feed_data]

    def publish_to_eitaa(self, message: str) -> bool:
        if not self.eitaa_enabled or not self.eitaa:
            return False
        result = self.eitaa.send(message)
        if result:
            self.logger.info("Eitaa publish successful.")
            return True
        self.logger.error("Eitaa publish failed.")
        return False

    def publish_to_pwa(self, feed_data: Any) -> bool:
        if not self.pwa_enabled or not self.pwa:
            return False
        try:
            path = self.pwa.publish(self._articles(feed_data))
            self.logger.info("PWA JSON datasource updated: %s", path)
            return True
        except Exception as exc:
            self.logger.error("PWA publish failed: %s", exc, exc_info=True)
            return False

    def publish_to_rss(self, feed_data: Any) -> bool:
        if not self.rss_enabled or not self.rss:
            return False
        try:
            path = self.rss.publish(self._articles(feed_data))
            self.logger.info("RSS XML feed updated: %s", path)
            return True
        except Exception as exc:
            self.logger.error("RSS publish failed: %s", exc, exc_info=True)
            return False

    def publish_all(self, feed_data: Any) -> dict[str, bool]:
        """Publish one article collection independently to every enabled channel."""
        return {
            "pwa": self.publish_to_pwa(feed_data) if self.pwa_enabled else False,
            "rss": self.publish_to_rss(feed_data) if self.rss_enabled else False,
        }

    def stop(self) -> bool:
        self.logger.info("Publisher module stopped.")
        return True
