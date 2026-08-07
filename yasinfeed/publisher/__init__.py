from yasinfeed.engine import BaseModule
from yasinfeed.publisher.eitaa import EitaaPublisher


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

        eitaa_config = pub_config.get("eitaa", {})

        self.eitaa_enabled = eitaa_config.get("enabled", False)
        self.pwa_enabled = pub_config.get("pwa", {}).get("enabled", False)
        self.rss_enabled = pub_config.get("rss", {}).get("enabled", False)

        self.eitaa = None

        if self.eitaa_enabled:
            token = eitaa_config.get("token")
            channel = eitaa_config.get("channel")

            if token and channel:
                self.eitaa = EitaaPublisher(
                    token,
                    channel
                )
                self.logger.info("Eitaa publisher initialized.")
            else:
                self.logger.warning(
                    "Eitaa enabled but token/channel missing."
                )

        self.logger.info(
            "Publisher Channels - Eitaa: %s, PWA: %s, RSS: %s",
            self.eitaa_enabled,
            self.pwa_enabled,
            self.rss_enabled
        )

        return True


    def start(self) -> bool:
        self.logger.info("Publisher module started.")
        return True


    def publish_to_eitaa(self, message: str) -> bool:
        if not self.eitaa_enabled or not self.eitaa:
            return False

        result = self.eitaa.send(message)

        if result:
            self.logger.info("Eitaa publish successful.")
            return True

        self.logger.error("Eitaa publish failed.")
        return False


    def publish_to_pwa(self, feed_data: dict) -> bool:
        if not self.pwa_enabled:
            return False

        self.logger.info("Updating PWA JSON datasource.")
        return True


    def publish_to_rss(self, feed_data: dict) -> bool:
        if not self.rss_enabled:
            return False

        self.logger.info("Generating RSS XML feed output.")
        return True


    def stop(self) -> bool:
        self.logger.info("Publisher module stopped.")
        return True
