import time
import threading
from contextlib import contextmanager
import functools
from typing import Dict, Any, Optional

class Metrics:
    """
    Thread-safe, extensible, and high-performance metrics registry for YasinFeed.
    Enables tracking of runtime stats, performance timing, and subsystem error metrics.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._errors: Dict[str, Any] = {}

    def inc(self, name: str, value: int = 1) -> None:
        """Atomically increments a counter metric."""
        with self._lock:
            self._data[name] = self._data.get(name, 0) + value

    def set(self, name: str, value: Any) -> None:
        """Atomically sets a metric value."""
        with self._lock:
            self._data[name] = value

    def get(self, name: str) -> Any:
        """Atomically retrieves a metric value."""
        with self._lock:
            return self._data.get(name)

    def all(self) -> Dict[str, Any]:
        """Returns a snapshot of all standard metrics."""
        with self._lock:
            snapshot = dict(self._data)
            # Merge error information dynamically if it has entries
            if self._errors:
                snapshot["_error_details"] = dict(self._errors)
            return snapshot

    @contextmanager
    def timing(self, name: str):
        """
        Context manager to measure the execution time of a block of code.
        Updates latency, peak, and average duration metrics.
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            with self._lock:
                # Update last execution time
                self._data[f"{name}_last_duration_seconds"] = round(duration, 4)
                # Keep cumulative run times and averages
                count_key = f"{name}_executions_total"
                total_key = f"{name}_duration_seconds_total"
                self._data[count_key] = self._data.get(count_key, 0) + 1
                self._data[total_key] = round(self._data.get(total_key, 0.0) + duration, 4)
                # Update average
                self._data[f"{name}_average_duration_seconds"] = round(
                    self._data[total_key] / self._data[count_key], 4
                )

    def time_func(self, name: str):
        """Decorator to measure function execution time."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.timing(name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def record_error(self, component: str, error_type: str, message: str) -> None:
        """
        Records a detailed error event and increments error counters.
        """
        self.inc("total_errors")
        self.inc(f"errors_{component}_total")
        with self._lock:
            self._errors[component] = {
                "type": error_type,
                "message": message,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

    def get_errors(self) -> Dict[str, Any]:
        """Returns the dictionary containing the last errors recorded per component."""
        with self._lock:
            return dict(self._errors)
