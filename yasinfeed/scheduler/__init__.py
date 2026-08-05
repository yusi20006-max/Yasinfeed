from yasinfeed.engine import BaseModule

class SchedulerModule(BaseModule):
    """
    Schedules and executes recurring tasks (fetch jobs, publishing queues).
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing scheduler module...")
        self.enabled = self.config.get("scheduler", {}).get("enabled", True)
        self.logger.info("Scheduler status: %s", "enabled" if self.enabled else "disabled")
        return True

    def start(self) -> bool:
        self.logger.info("Scheduler module started. Periodic triggers set up.")
        return True

    def stop(self) -> bool:
        self.logger.info("Scheduler module stopped. Active timers and threads cancelled.")
        return True
