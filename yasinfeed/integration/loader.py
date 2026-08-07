import importlib.util
import os
import sys
import logging
from typing import List, Any
from yasinfeed.integration.providers import BaseIntegrationProvider

logger = logging.getLogger("yasinfeed.integration.loader")

class PluginLoader:
    """
    Handles dynamic discovery, compilation, and initialization of external
    Yasin Feed plugins and extensions. Fully compatible with Linux and Termux on Android.
    """

    @staticmethod
    def load_plugin_from_file(file_path: str) -> List[BaseIntegrationProvider]:
        """
        Dynamically loads a Python module from a given file path and instantiates
        any registered BaseIntegrationProvider subclasses defined inside.
        """
        if not os.path.exists(file_path):
            logger.error("Plugin file not found: %s", file_path)
            return []

        module_name = os.path.basename(file_path).replace(".py", "")
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.error("Failed to create module spec for: %s", file_path)
                return []

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            providers_loaded = []

            # Inspect the module for classes that inherit from BaseIntegrationProvider
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseIntegrationProvider) and attr is not BaseIntegrationProvider:
                    try:
                        # Instantiate the provider with default name and config if any
                        provider_inst = attr(name=attr_name.lower())
                        providers_loaded.append(provider_inst)
                    except Exception as ex:
                        logger.error("Failed to instantiate provider class %s from file: %s", attr_name, ex)

            # Check for a module-level register/setup hook
            if hasattr(module, "register_plugin"):
                try:
                    registered_from_hook = module.register_plugin()
                    if isinstance(registered_from_hook, list):
                        providers_loaded.extend(registered_from_hook)
                    elif isinstance(registered_from_hook, BaseIntegrationProvider):
                        providers_loaded.append(registered_from_hook)
                except Exception as ex:
                    logger.error("Failed calling 'register_plugin' hook in %s: %s", module_name, ex)

            return providers_loaded

        except Exception as e:
            logger.error("Error loading dynamic plugin from file %s: %s", file_path, e, exc_info=True)
            return []

    @classmethod
    def load_plugins_from_directory(cls, dir_path: str) -> List[BaseIntegrationProvider]:
        """
        Discovers all Python files in a directory and dynamically imports them
        as integration provider plugins.
        """
        if not os.path.isdir(dir_path):
            logger.debug("Plugin directory not found or is not a folder: %s", dir_path)
            return []

        all_providers = []
        for filename in sorted(os.listdir(dir_path)):
            if filename.endswith(".py") and filename != "__init__.py":
                file_path = os.path.join(dir_path, filename)
                logger.info("Discovering dynamic plugin file: %s", file_path)
                loaded = cls.load_plugin_from_file(file_path)
                all_providers.extend(loaded)

        return all_providers
