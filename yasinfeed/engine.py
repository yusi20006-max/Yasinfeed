import logging
import signal
import sys
import time
import threading
from typing import Dict, List, Type

from yasinfeed.config import load_config
from yasinfeed.logging import setup_logging

# We will define the BaseModule here or import it
class BaseModule:
    """
    Base class for all YasinFeed modules.
    Provides standard lifecycle hooks: initialize, start, stop.
    """
    def __init__(self, engine: 'YasinFeedEngine'):
        self.engine = engine
        self.config = engine.config
        # Standardized logger for each module
        self.logger = logging.getLogger(f"yasinfeed.{self.get_module_name()}")

    @classmethod
    def get_module_name(cls) -> str:
        name = cls.__name__.lower()
        if name.endswith("module"):
            name = name[:-6]
        return name

    def initialize(self) -> bool:
        """Initialize resources, prepare dependencies."""
        self.logger.debug("Initializing module...")
        return True

    def start(self) -> bool:
        """Start the background execution/tasks."""
        self.logger.debug("Starting module...")
        return True

    def stop(self) -> bool:
        """Gracefully stop tasks and release resources."""
        self.logger.debug("Stopping module...")
        return True


class YasinFeedEngine:
    """
    Core engine of YasinFeed.
    Responsible for module loading, configuration management, logging setup,
    and managing the application lifecycle (initialize, start, stop).
    """
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config: dict = {}
        self.logger: logging.Logger = logging.getLogger("yasinfeed.engine")
        self.modules: Dict[str, BaseModule] = {}
        self.module_classes: List[Type[BaseModule]] = []
        self._running = False
        self._shutdown_event = threading.Event()

    def register_module(self, module_cls: Type[BaseModule]):
        """Registers a module class to be loaded by the engine."""
        self.module_classes.append(module_cls)

    def initialize(self) -> bool:
        """
        Loads configuration, sets up logging, and initializes registered modules.
        Returns True if successful, False otherwise.
        """
        try:
            # 1. Load config
            self.config = load_config(self.config_path)

            # 2. Setup logging
            self.logger = setup_logging(self.config)
            self.logger.info("Initializing YasinFeed Engine...")

            # 3. Import and load all modules in designated order
            # To avoid circular imports, we can import them dynamically inside initialize
            from yasinfeed.monitoring import MonitoringModule
            from yasinfeed.integration import IntegrationModule
            from yasinfeed.storage import StorageModule
            from yasinfeed.models import ModelsModule
            from yasinfeed.auth import AuthModule
            from yasinfeed.rewrite import RewriteModule
            from yasinfeed.fetch import FetchModule
            from yasinfeed.publisher import PublisherModule
            from yasinfeed.scheduler import SchedulerModule
            from yasinfeed.api import ApiModule

            # Register them in the correct dependency order
            self.register_module(MonitoringModule)
            self.register_module(IntegrationModule)
            self.register_module(StorageModule)
            self.register_module(ModelsModule)
            self.register_module(AuthModule)
            self.register_module(RewriteModule)
            self.register_module(FetchModule)
            self.register_module(PublisherModule)
            self.register_module(SchedulerModule)
            self.register_module(ApiModule)

            # Instantiate registered modules
            for m_cls in self.module_classes:
                name = m_cls.get_module_name()
                try:
                    module_inst = m_cls(self)
                    self.modules[name] = module_inst
                except Exception as ex:
                    self.logger.error("Failed to instantiate module %s: %s", name, ex, exc_info=True)
                    return False

            # Initialize all modules in registration order
            for name, module in self.modules.items():
                self.logger.info("Initializing module: %s", name)
                success = module.initialize()
                if not success:
                    self.logger.error("Failed to initialize module: %s", name)
                    return False

            self.logger.info("YasinFeed Engine initialization completed successfully.")
            return True

        except Exception as e:
            # Fallback prints in case logging setup itself failed
            print(f"Critical error during engine initialization: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def start(self):
        """
        Starts all initialized modules and begins main loop.
        Handles OS signals for clean shutdown.
        """
        if self._running:
            self.logger.warning("Engine is already running.")
            return

        self.logger.info("Starting YasinFeed Engine...")
        self._running = True
        self._shutdown_event.clear()

        # Start all modules in order
        for name, module in self.modules.items():
            self.logger.info("Starting module: %s", name)
            success = module.start()
            if not success:
                self.logger.error("Module %s failed to start. Initiating shutdown.", name)
                self.stop()
                return

        self.logger.info("YasinFeed Core is up and running.")

        # Main thread wait loop
        try:
            while not self._shutdown_event.is_set():
                time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Shutdown signal received on main thread.")
            self.stop()

    def stop(self):
        """
        Gracefully stops all running modules in reverse order.
        """
        if not self._running:
            return

        self.logger.info("Stopping YasinFeed Engine...")
        self._running = False
        self._shutdown_event.set()

        # Stop all modules in reverse order
        for name, module in reversed(list(self.modules.items())):
            self.logger.info("Stopping module: %s", name)
            try:
                success = module.stop()
                if not success:
                    self.logger.warning("Module %s failed to stop cleanly.", name)
            except Exception as e:
                self.logger.error("Error stopping module %s: %s", name, e, exc_info=True)

        self.logger.info("YasinFeed Engine stopped cleanly.")


def handle_signals(engine: YasinFeedEngine):
    """Register system signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        signal_name = "SIGINT" if sig == signal.SIGINT else "SIGTERM"
        engine.logger.info("Signal %s received. Shutting down...", signal_name)
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
