import os
import logging
import unittest
from yasinfeed.logging import setup_logging

class TestLogging(unittest.TestCase):
    def test_setup_logging_console_and_file(self):
        log_file = "test_yasinfeed.log"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except OSError:
                pass

        config = {
            "logging": {
                "level": "DEBUG",
                "file_path": log_file,
                "console": True
            }
        }

        # Setup logging
        logger = setup_logging(config)
        self.assertEqual(logger.level, logging.DEBUG)

        # Check root logger handlers
        root_logger = logging.getLogger()
        handler_types = [type(h) for h in root_logger.handlers]
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertIn(logging.FileHandler, handler_types)

        # Clean up handlers so we don't pollute other tests or keep files locked
        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

        # Clean up files
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except OSError:
                pass

    def test_setup_logging_no_file(self):
        config = {
            "logging": {
                "level": "WARNING",
                "file_path": None,
                "console": True
            }
        }

        logger = setup_logging(config)
        self.assertEqual(logger.level, logging.WARNING)

        root_logger = logging.getLogger()
        handler_types = [type(h) for h in root_logger.handlers]
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertNotIn(logging.FileHandler, handler_types)

        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

if __name__ == "__main__":
    unittest.main()
