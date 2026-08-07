import logging
from typing import Dict, List, Any, Callable, Optional

from yasinfeed.engine import BaseModule
from yasinfeed.integration.providers import BaseIntegrationProvider


class IntegrationModule(BaseModule):
    """
    Decoupled integration module acting as the foundational communication plane.
    Coordinates event hooks, dynamic providers, and future Yasin Agent/Hub compatibility.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing Integration module...")
        self.providers: Dict[str, BaseIntegrationProvider] = {}
        self.hooks: Dict[str, List[Callable[..., Any]]] = {
            "on_startup": [],
            "on_shutdown": [],
            "on_pipeline_start": [],
            "on_pipeline_complete": [],
            "on_article_fetched": [],
            "on_article_processed": [],
            "on_error": []
        }

        # Setup dynamic plugin loaders if specified
        self.plugin_configs = self.config.get("integration", {}).get("plugins", [])
        return True

    def start(self) -> bool:
        self.logger.info("Integration module started.")
        self.trigger_event("on_startup")
        return True

    def stop(self) -> bool:
        self.logger.info("Integration module stopping...")
        self.trigger_event("on_shutdown")
        return True

    # --- Hook & Event Callback Registration ---
    def register_hook(self, event_name: str, callback: Callable[..., Any]) -> None:
        """Dynamically registers a callable event hook handler."""
        if event_name not in self.hooks:
            self.hooks[event_name] = []
        self.hooks[event_name].append(callback)
        self.logger.debug("Hook registered on event: %s", event_name)

    def unregister_hook(self, event_name: str, callback: Callable[..., Any]) -> None:
        """Removes a dynamically registered hook handler."""
        if event_name in self.hooks and callback in self.hooks[event_name]:
            self.hooks[event_name].remove(callback)
            self.logger.debug("Hook unregistered from event: %s", event_name)

    # --- Provider Registration ---
    def register_provider(self, provider: BaseIntegrationProvider) -> None:
        """Registers an integration provider instance."""
        self.providers[provider.name] = provider
        provider.on_register()
        self.logger.info("Integration provider registered: %s", provider.name)

    def get_provider(self, name: str) -> Optional[BaseIntegrationProvider]:
        """Retrieves a registered provider by name."""
        return self.providers.get(name)

    def list_providers(self) -> List[BaseIntegrationProvider]:
        """Lists all active integration providers."""
        return list(self.providers.values())

    # --- Event Dispatching Engine ---
    def trigger_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Safely dispatches event notices to all registered hook callables and
        active Integration Providers in a non-blocking/isolated fashion.
        """
        self.logger.debug("Triggering integration event: %s", event_name)

        # 1. Dispatch to local registered hook callables
        local_callbacks = self.hooks.get(event_name, [])
        for cb in list(local_callbacks):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                self.logger.error("Error in hook callback for %s: %s", event_name, e, exc_info=True)

        # 2. Propagate to active integration providers
        for p_name, provider in list(self.providers.items()):
            try:
                provider.on_event(event_name, *args, **kwargs)
            except Exception as e:
                self.logger.error("Error in provider '%s' processing event %s: %s", p_name, event_name, e, exc_info=True)
