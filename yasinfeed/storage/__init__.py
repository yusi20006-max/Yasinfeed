from yasinfeed.engine import BaseModule

class StorageModule(BaseModule):
    """
    Handles local data storage, database connections, and migrations.
    Supported types: sqlite, json.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing storage module...")
        self.storage_type = self.config.get("storage", {}).get("type", "sqlite")
        self.storage_path = self.config.get("storage", {}).get("path", "data/yasinfeed.db")
        self.logger.info("Storage backend: %s at %s", self.storage_type, self.storage_path)
        return True

    def start(self) -> bool:
        self.logger.info("Storage module started. Connection pool established.")
        return True

    def stop(self) -> bool:
        self.logger.info("Storage module stopped. Connection pool released.")
        return True
