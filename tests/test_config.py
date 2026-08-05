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

if __name__ == "__main__":
    unittest.main()
