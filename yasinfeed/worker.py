"""Background worker pool with graceful stop semantics."""

from __future__ import annotations

import logging
import threading
from typing import Callable, List, Optional

from yasinfeed.queue import FeedQueue, QueueEmpty

logger = logging.getLogger("yasinfeed.worker")


class WorkerPool:
    """
    Fixed-size daemon worker pool backed by FeedQueue.

    stop() unblocks workers via sentinel no-ops, joins threads with a
    timeout, and clears the thread list so start() can be called again.
    """

    def __init__(self, workers: int = 2, join_timeout: float = 3.0) -> None:
        if workers < 1:
            raise ValueError("workers must be >= 1")
        self.queue = FeedQueue()
        self.workers = workers
        self.join_timeout = join_timeout
        self.threads: List[threading.Thread] = []
        self.running = False
        self._lock = threading.Lock()

    def submit(self, job: Callable[[], None]) -> None:
        if not callable(job):
            raise TypeError("job must be callable")
        self.queue.push(job)

    def _worker(self) -> None:
        while True:
            with self._lock:
                if not self.running:
                    break
            try:
                job = self.queue.pop(timeout=0.2)
            except QueueEmpty:
                with self._lock:
                    if not self.running:
                        break
                continue
            try:
                job()
            except Exception:
                logger.exception("Worker job failed")

    def start(self) -> None:
        with self._lock:
            if self.running:
                return
            self.running = True
            self.threads = []
            for i in range(self.workers):
                t = threading.Thread(
                    target=self._worker,
                    daemon=True,
                    name=f"YasinFeedWorker-{i}",
                )
                t.start()
                self.threads.append(t)

    def stop(self) -> None:
        """Signal workers to exit, unblock queue, and join threads."""
        with self._lock:
            if not self.running:
                return
            self.running = False
            n = len(self.threads)

        for _ in range(max(n, self.workers)):
            self.queue.push(lambda: None)

        for t in list(self.threads):
            t.join(timeout=self.join_timeout)
            if t.is_alive():
                logger.warning(
                    "Worker thread %s did not exit within %.1fs",
                    t.name,
                    self.join_timeout,
                )

        with self._lock:
            self.threads = []
