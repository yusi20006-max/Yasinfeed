import unittest
import importlib
import sys
from yasinfeed.engine import BaseModule, YasinFeedEngine

class TestArchitecture(unittest.TestCase):
    """
    Validates standard package structure and architectural boundaries.
    """
    def test_required_modules_exist(self):
        # We need to verify the existence of expected core modules:
        # api, fetch, rewrite, storage, scheduler, publisher, models, auth.
        expected_modules = ["api", "fetch", "rewrite", "storage", "scheduler", "publisher", "models", "auth"]

        for module_name in expected_modules:
            try:
                module = importlib.import_module(f"yasinfeed.{module_name}")
                self.assertIsNotNone(module)
            except ImportError as e:
                self.fail(f"Required architecture module 'yasinfeed.{module_name}' is missing: {e}")

    def test_modules_are_subclasses_of_base_module(self):
        # Verify that loaded classes are subclass of BaseModule
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        success = engine.initialize()
        self.assertTrue(success)

        expected_modules = ["storage", "models", "auth", "rewrite", "fetch", "publisher", "scheduler", "api"]
        for m_name in expected_modules:
            self.assertIn(m_name, engine.modules, f"Module '{m_name}' not loaded in engine")
            module_inst = engine.modules[m_name]
            self.assertTrue(isinstance(module_inst, BaseModule), f"Module '{m_name}' does not inherit from BaseModule")

    def test_no_unwanted_ecosystem_imports(self):
        # Ensure that no modules import forbidden classes or frameworks (like YasinCLI, YasinHub, Yasin-Agent)
        forbidden_keywords = ["yasinhub", "yasin_agent", "yasincli", "yasin-agent"]

        # We will scan the loaded sys.modules for any modules loaded that shouldn't be
        for loaded_module_name in sys.modules:
            for keyword in forbidden_keywords:
                self.assertNotIn(keyword, loaded_module_name.lower(),
                                 f"Forbidden module or package '{loaded_module_name}' is imported!")

if __name__ == "__main__":
    unittest.main()
