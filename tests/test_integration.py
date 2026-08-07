import os
import tempfile
import unittest
from typing import Dict, Any, Optional

from yasinfeed.engine import YasinFeedEngine
from yasinfeed.models import Article
from yasinfeed.integration import IntegrationModule
from yasinfeed.integration.providers import (
    BaseIntegrationProvider,
    HubIntegrationProvider,
    AgentIntegrationProvider
)
from yasinfeed.integration.loader import PluginLoader


# 1. Custom mock providers for testing
class MockBaseProvider(BaseIntegrationProvider):
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.registered = False
        self.events_received = []

    def on_register(self) -> None:
        self.registered = True

    def on_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        self.events_received.append((event_name, args, kwargs))


class MockHubProvider(HubIntegrationProvider):
    def __init__(self, name: str):
        super().__init__(name)
        self.registered = False
        self.events_received = []

    def on_register(self) -> None:
        self.registered = True

    def on_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        self.events_received.append((event_name, args, kwargs))

    def register_routes(self) -> Dict[str, str]:
        return {"/hub/control": "MockHubController"}

    def notify_hub_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        return True


class MockAgentProvider(AgentIntegrationProvider):
    def __init__(self, name: str):
        super().__init__(name)
        self.registered = False
        self.events_received = []

    def on_register(self) -> None:
        self.registered = True

    def on_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        self.events_received.append((event_name, args, kwargs))

    def dispatch_agent_task(self, task_type: str, payload: Dict[str, Any], urgency: str = "normal") -> Dict[str, Any]:
        return {"task_id": "agent-t-1", "status": "dispatched", "urgency": urgency}

    def retrieve_agent_review(self, article_id: str) -> Optional[Dict[str, Any]]:
        return {"article_id": article_id, "curation": "approved"}


class TestIntegrationSystem(unittest.TestCase):

    def test_provider_registration_and_event_hooks(self) -> None:
        """Test registering providers and triggering hooks/events."""
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        engine.initialize()

        integration_mod = engine.modules["integration"]
        self.assertTrue(isinstance(integration_mod, IntegrationModule))

        # Instantiate mock providers
        base_prov = MockBaseProvider(name="mock_base")
        hub_prov = MockHubProvider(name="mock_hub")
        agent_prov = MockAgentProvider(name="mock_agent")

        # Register providers
        integration_mod.register_provider(base_prov)
        integration_mod.register_provider(hub_prov)
        integration_mod.register_provider(agent_prov)

        self.assertTrue(base_prov.registered)
        self.assertTrue(hub_prov.registered)
        self.assertTrue(agent_prov.registered)

        # Retrieve and list providers
        self.assertEqual(integration_mod.get_provider("mock_base"), base_prov)
        self.assertEqual(len(integration_mod.list_providers()), 3)

        # Dynamic callback hook registration
        callback_fired = []

        def sample_hook_handler(*args, **kwargs):
            callback_fired.append((args, kwargs))

        integration_mod.register_hook("on_pipeline_complete", sample_hook_handler)

        # Trigger event
        dummy_article_payload = {"id": "art-1", "title": "Test Title"}
        integration_mod.trigger_event("on_pipeline_complete", dummy_article_payload, status="success")

        # Verify dynamic callback was executed
        self.assertEqual(len(callback_fired), 1)
        self.assertEqual(callback_fired[0][0][0], dummy_article_payload)
        self.assertEqual(callback_fired[0][1]["status"], "success")

        # Verify providers also received the propagated event
        for prov in (base_prov, hub_prov, agent_prov):
            self.assertEqual(len(prov.events_received), 1)
            self.assertEqual(prov.events_received[0][0], "on_pipeline_complete")
            self.assertEqual(prov.events_received[0][1][0], dummy_article_payload)
            self.assertEqual(prov.events_received[0][2]["status"], "success")

        # Unregister hook
        integration_mod.unregister_hook("on_pipeline_complete", sample_hook_handler)
        integration_mod.trigger_event("on_pipeline_complete", dummy_article_payload)
        # Callback fired count should remain 1
        self.assertEqual(len(callback_fired), 1)

    def test_dynamic_plugin_loader(self) -> None:
        """Test the PluginLoader dynamically loads providers and calls register hooks from a dynamic python file."""
        # Create a mock plugin file as temporary file
        plugin_code = """
from yasinfeed.integration.providers import BaseIntegrationProvider

class DynamicLoadedProvider(BaseIntegrationProvider):
    def on_register(self) -> None:
        self.on_register_called = True

    def on_event(self, event_name: str, *args, **kwargs) -> None:
        pass

def register_plugin():
    return [DynamicLoadedProvider(name="dynamic_class")]
"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write(plugin_code)
            tmp_path = f.name

        try:
            loaded_providers = PluginLoader.load_plugin_from_file(tmp_path)
            self.assertEqual(len(loaded_providers), 2)  # One from the class discovery, one from register_plugin hook

            # Verify base behaviors
            provider = loaded_providers[0]
            self.assertTrue(isinstance(provider, BaseIntegrationProvider))
            self.assertEqual(provider.name, "dynamicloadedprovider")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_future_agent_compatibility_interfaces(self) -> None:
        """Test specialized interfaces designed for Yasin-Agent planning compatibility."""
        agent_prov = MockAgentProvider(name="agent_prov")

        # Test agent planning/decision schemas and tasks dispatching
        task_res = agent_prov.dispatch_agent_task("rewrite_planning", {"theme": "technical_summary"}, urgency="high")
        self.assertEqual(task_res["status"], "dispatched")
        self.assertEqual(task_res["urgency"], "high")

        # Test retrieving agent review metrics
        review = agent_prov.retrieve_agent_review("art-999")
        self.assertEqual(review["article_id"], "art-999")
        self.assertEqual(review["curation"], "approved")

    def test_backward_compatibility_engine_lifecycle(self) -> None:
        """Test that adding the IntegrationModule does not alter engine setup and standard lifecycle operations."""
        engine = YasinFeedEngine(config_path="/path/to/nonexistent/config.yaml")
        success = engine.initialize()
        self.assertTrue(success)

        self.assertIn("integration", engine.modules)
        integration_mod = engine.modules["integration"]
        self.assertTrue(isinstance(integration_mod, IntegrationModule))


if __name__ == "__main__":
    unittest.main()
