import json
import os
import time
from typing import Dict, Any, Optional

class StructuredEventLogger:
    """
    High-performance, pure-Python, zero-dependency structured event logging engine.
    Formats and writes standard logs with json structures to structured outputs.
    Perfect for microservice observability and agent/hub telemetry consumption.
    """

    def __init__(self, log_path: str = "config/events.json"):
        self.log_path = log_path
        try:
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        except Exception:
            # Fallback to local file if parent directory can't be created
            self.log_path = "events.json"

    def log_event(self, event_type: str, severity: str, module: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Emits a structured event log in standard JSON format.
        Appends the serialized event to the specified JSON Lines log file.
        """
        event = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "severity": severity.upper(),
            "module": module,
            "message": message,
            "details": details or {}
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            # Fallback gracefully to standard stream if disk writing fails on Termux
            pass
