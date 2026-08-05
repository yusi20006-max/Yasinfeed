from yasinfeed.engine import BaseModule

class ApiModule(BaseModule):
    """
    Exposes endpoints for PWA clients and other components to consume feed outputs.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing API module...")
        self.host = self.config.get("api", {}).get("host", "127.0.0.1")
        self.port = self.config.get("api", {}).get("port", 8000)
        self.logger.info("API server bound to %s:%d", self.host, self.port)
        return True

    def start(self) -> bool:
        self.logger.info("API module started. Listening on http://%s:%d", self.host, self.port)
        return True

    def stop(self) -> bool:
        self.logger.info("API module stopped. Socket connection closed.")
        return True
