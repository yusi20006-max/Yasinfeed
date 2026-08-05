import threading
from yasinfeed.queue import FeedQueue

class WorkerPool:

    def __init__(self, workers=2):
        self.queue = FeedQueue()
        self.workers = workers
        self.threads = []
        self.running = False

    def submit(self, job):
        self.queue.push(job)

    def _worker(self):
        while self.running:
            job = self.queue.pop()
            try:
                job()
            except Exception:
                pass

    def start(self):
        self.running = True
        for _ in range(self.workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        self.running = False
        for _ in self.threads:
            self.queue.push(lambda: None)
