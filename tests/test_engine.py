import unittest
import threading
import time
from yasinfeed.engine import YasinFeedEngine, BaseModule

class TestEngine(unittest.TestCase):
    def test_engine_initialization_and_modules(self):
        # Create an engine with fallback nonexistent config path to use defaults
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")

        # Initialize
        success = engine.initialize()
        self.assertTrue(success)

        # Verify all 7 required modules are present
        required_modules = ["storage", "models", "rewrite", "fetch", "publisher", "scheduler", "api"]
        for m_name in required_modules:
            self.assertIn(m_name, engine.modules)
            self.assertIsInstance(engine.modules[m_name], BaseModule)

    def tearDown(self):
        # Clean up logging handlers to avoid ResourceWarnings and clean up state
        import logging
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

        # Remove the generated log file
        import os
        for log_file in ["yasinfeed.log", "test_yasinfeed.log"]:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except OSError:
                    pass

    def test_engine_start_and_stop_lifecycle(self):
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        success = engine.initialize()
        self.assertTrue(success)

        # Avoid port collision by assigning port 0 (dynamic allocation)
        if "api" in engine.modules:
            engine.modules["api"].port = 0
        if "api" in engine.config:
            engine.config["api"]["port"] = 0

        # Let's run start in a background thread so we can stop it
        def run_engine():
            engine.start()

        thread = threading.Thread(target=run_engine)
        thread.start()

        # Let it run for a brief moment
        time.sleep(0.2)
        self.assertTrue(engine._running)

        # Stop engine
        engine.stop()
        thread.join(timeout=2.0)

        self.assertFalse(engine._running)

if __name__ == "__main__":
    unittest.main()
