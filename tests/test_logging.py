import os
import logging
import unittest
from yasinfeed.logging import setup_logging

class TestLogging(unittest.TestCase):
    def tearDown(self):
        # Ensure clean state after each test
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

    def test_output_formatting(self):
        import io
        import re
        log_capture = io.StringIO()

        config = {
            "logging": {
                "level": "INFO",
                "file_path": None,
                "console": True
            }
        }

        # Modify setup_logging slightly or capture its StreamHandler's output.
        # Since setup_logging sets StreamHandler to sys.stdout, we can temporarily patch sys.stdout
        # or we can inspect the formatter directly.
        logger = setup_logging(config)

        # Inspect formatters
        root_logger = logging.getLogger()
        has_correct_format = False
        for h in root_logger.handlers:
            if isinstance(h, logging.StreamHandler):
                formatter = h.formatter
                if formatter:
                    # check if format pattern matches the expected one
                    self.assertEqual(formatter._fmt, "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
                    self.assertEqual(formatter.datefmt, "%Y-%m-%d %H:%M:%S")
                    has_correct_format = True

        self.assertTrue(has_correct_format)

        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

    def test_log_level_hierarchy_and_filtering(self):
        # We'll configure logger to WARNING, log messages at INFO and ERROR,
        # and verify they filter appropriately using a list stream handler to capture logs.
        import io
        log_capture = io.StringIO()

        config = {
            "logging": {
                "level": "WARNING",
                "file_path": None,
                "console": False
            }
        }

        logger = setup_logging(config)
        self.assertEqual(logger.level, logging.WARNING)

        # Manually attach a StringIO stream handler for capture
        root_logger = logging.getLogger()
        capture_handler = logging.StreamHandler(log_capture)
        capture_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root_logger.addHandler(capture_handler)

        # Log messages of various levels
        logger.debug("This is DEBUG")
        logger.info("This is INFO")
        logger.warning("This is WARNING")
        logger.error("This is ERROR")

        # Flush the captured output
        capture_handler.flush()
        output = log_capture.getvalue()

        # Assertions
        self.assertNotIn("DEBUG", output)
        self.assertNotIn("INFO", output)
        self.assertIn("WARNING: This is WARNING", output)
        self.assertIn("ERROR: This is ERROR", output)

        # Clean up
        capture_handler.close()
        root_logger.removeHandler(capture_handler)

        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

    def test_setup_logging_empty_and_missing_config(self):
        # Empty config
        logger = setup_logging({})
        self.assertEqual(logger.level, logging.INFO) # default level is INFO

        root_logger = logging.getLogger()
        handler_types = [type(h) for h in root_logger.handlers]
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertIn(logging.FileHandler, handler_types) # default path is yasinfeed.log

        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)

        # Partially missing logging config
        config = {"logging": {}}
        logger = setup_logging(config)
        self.assertEqual(logger.level, logging.INFO)

        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)
        for log_file in ["test_yasinfeed.log", "yasinfeed.log"]:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except OSError:
                    pass

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
