from yasinfeed.engine import BaseModule

class PublisherModule(BaseModule):
    """
    Coordinates publishing to output channels:
    - Eitaa publishing
    - PWA data source
    - RSS output
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing publisher module...")
        pub_config = self.config.get("publisher", {})
        self.eitaa_enabled = pub_config.get("eitaa", {}).get("enabled", False)
        self.pwa_enabled = pub_config.get("pwa", {}).get("enabled", False)
        self.rss_enabled = pub_config.get("rss", {}).get("enabled", False)

        self.logger.info("Publisher Channels Configured - Eitaa: %s, PWA: %s, RSS: %s",
                         self.eitaa_enabled, self.pwa_enabled, self.rss_enabled)
        return True

    def start(self) -> bool:
        self.logger.info("Publisher module started.")
        return True

    def publish_to_eitaa(self, message: str) -> bool:
        if not self.eitaa_enabled:
            self.logger.debug("Eitaa publishing skipped: disabled in config.")
            return False
        self.logger.info("Publishing rewritten feed to Eitaa: %s", message[:50])
        return True

    def publish_to_pwa(self, feed_data: dict) -> bool:
        if not self.pwa_enabled:
            self.logger.debug("PWA feed update skipped: disabled in config.")
            return False
        self.logger.info("Updating PWA JSON datasource.")
        return True

    def publish_to_rss(self, feed_data: dict) -> bool:
        if not self.rss_enabled:
            self.logger.debug("RSS output generation skipped: disabled in config.")
            return False
        self.logger.info("Generating RSS XML feed output.")
        return True

    def stop(self) -> bool:
        self.logger.info("Publisher module stopped.")
        return True
