import os
import unittest
from unittest.mock import patch
from yasinfeed.config import load_config, DEFAULT_CONFIG, cast_value

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Clear any environment variables starting with YASINFEED_ to keep tests pure
        self.original_env = {}
        for key in list(os.environ.keys()):
            if key.startswith("YASINFEED_"):
                self.original_env[key] = os.environ[key]
                del os.environ[key]

    def tearDown(self):
        # Restore environment variables
        for key in list(os.environ.keys()):
            if key.startswith("YASINFEED_"):
                del os.environ[key]
        for key, val in self.original_env.items():
            os.environ[key] = val

    def test_cast_value(self):
        self.assertEqual(cast_value("123", 10), 123)
        self.assertEqual(cast_value("invalid", 10), 10)
        self.assertEqual(cast_value("true", False), True)
        self.assertEqual(cast_value("FALSE", True), False)
        self.assertEqual(cast_value("some_str", "default"), "some_str")

    def test_load_default_config_when_file_not_exist(self):
        # Passing an invalid path should fallback gracefully to default values
        config = load_config("/path/to/nonexistent/config.yaml")
        self.assertEqual(config["app"]["name"], "YasinFeed")
        self.assertEqual(config["api"]["port"], 8000)

    def test_direct_env_overrides(self):
        os.environ["YASINFEED_PORT"] = "9999"
        os.environ["YASINFEED_LOG_LEVEL"] = "DEBUG"
        os.environ["YASINFEED_ENV"] = "staging"

        config = load_config("/path/to/nonexistent/config.yaml")
        self.assertEqual(config["api"]["port"], 9999)
        self.assertEqual(config["logging"]["level"], "DEBUG")
        self.assertEqual(config["app"]["env"], "staging")

    def test_nested_env_overrides(self):
        os.environ["YASINFEED__PUBLISHER__EITAA__ENABLED"] = "true"
        os.environ["YASINFEED__FETCH__INTERVAL_SECONDS"] = "60"

        config = load_config("/path/to/nonexistent/config.yaml")
        self.assertEqual(config["publisher"]["eitaa"]["enabled"], True)
        self.assertEqual(config["fetch"]["interval_seconds"], 60)

    def test_cast_value_auto_detection_when_default_none(self):
        # Test bool detection
        self.assertTrue(cast_value("true", None))
        self.assertTrue(cast_value("YES", None))
        self.assertTrue(cast_value("on", None))
        self.assertFalse(cast_value("false", None))
        self.assertFalse(cast_value("NO", None))
        self.assertFalse(cast_value("off", None))

        # Test integer detection
        self.assertEqual(cast_value("456", None), 456)
        self.assertEqual(cast_value("-12", None), -12)

        # Test float detection
        self.assertEqual(cast_value("3.1415", None), 3.1415)
        self.assertEqual(cast_value("-0.005", None), -0.005)

        # Test fallback to string
        self.assertEqual(cast_value("hello", None), "hello")
        self.assertEqual(cast_value("123hello", None), "123hello")

        # Non-string input should return as-is
        self.assertEqual(cast_value(999, None), 999)

    def test_dynamic_deep_nested_env_overrides(self):
        # Keys not predefined in DEFAULT_CONFIG should be correctly parsed, and types auto-detected
        os.environ["YASINFEED__PUBLISHER__EITAA__SUB_CONFIG__ENABLED"] = "true"
        os.environ["YASINFEED__PUBLISHER__EITAA__SUB_CONFIG__RETRY_COUNT"] = "5"
        os.environ["YASINFEED__PUBLISHER__EITAA__SUB_CONFIG__TIMEOUT"] = "15.5"
        os.environ["YASINFEED__PUBLISHER__EITAA__SUB_CONFIG__NAME"] = "my_eitaa_sub"

        config = load_config("/path/to/nonexistent/config.yaml")
        sub = config["publisher"]["eitaa"]["sub_config"]
        self.assertEqual(sub["enabled"], True)
        self.assertEqual(sub["retry_count"], 5)
        self.assertEqual(sub["timeout"], 15.5)
        self.assertEqual(sub["name"], "my_eitaa_sub")

if __name__ == "__main__":
    unittest.main()
