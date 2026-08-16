"""Thread-safe job queue for WorkerPool."""

from __future__ import annotations

from queue import Empty, Queue
from typing import Any, Optional


class FeedQueue:
    """Thin wrapper around queue.Queue with timeout-aware pop."""

    def __init__(self) -> None:
        self.q: Queue = Queue()

    def push(self, item: Any) -> None:
        self.q.put(item)

    def pop(self, timeout: Optional[float] = None) -> Any:
        """
        Pop next item.

        If timeout is None, block until an item is available.
        If timeout is a float, raise queue.Empty when the timeout expires.
        """
        if timeout is None:
            return self.q.get()
        return self.q.get(timeout=timeout)

    def size(self) -> int:
        return self.q.qsize()


# Re-export Empty for callers that need to catch timeout
QueueEmpty = Empty
