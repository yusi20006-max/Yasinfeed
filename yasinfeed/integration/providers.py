from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseIntegrationProvider(ABC):
    """
    Abstract base class for all Yasin Feed integration providers.
    Provides standardized hook endpoints for wider ecosystem compatibility.
    """
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def on_register(self) -> None:
        """Called when the provider is loaded and registered in the integration manager."""
        pass

    @abstractmethod
    def on_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Receives notification of system events.
        Enables non-blocking reaction to engine lifecycle milestones.
        """
        pass


class HubIntegrationProvider(BaseIntegrationProvider):
    """
    Provider interface specializing in Yasin-Hub communication,
    process control notifications, and router registration.
    """
    def on_register(self) -> None:
        pass

    def on_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def register_routes(self) -> Dict[str, str]:
        """Returns REST endpoint routes mapping to downstream handlers."""
        pass

    @abstractmethod
    def notify_hub_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Sends service heartbeats or diagnostic telemetry to Yasin-Hub."""
        pass


class AgentIntegrationProvider(BaseIntegrationProvider):
    """
    Provider interface specializing in Yasin-Agent workflows,
    dispatching articles for AI planning, and posting curation reviews.
    """
    def on_register(self) -> None:
        pass

    def on_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def dispatch_agent_task(self, task_type: str, payload: Dict[str, Any], urgency: str = "normal") -> Dict[str, Any]:
        """Dispatches an analytical or creative task to a downstream Yasin-Agent."""
        pass

    @abstractmethod
    def retrieve_agent_review(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves outstanding curation decisions, summary ratings, or rewrite planning instructions."""
        pass
