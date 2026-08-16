import threading
import time
import unittest

from yasinfeed.worker import WorkerPool


class TestWorker(unittest.TestCase):

    def test_worker(self):
        result = []
        pool = WorkerPool(1)
        pool.start()
        pool.submit(lambda: result.append("ok"))
        time.sleep(0.3)
        pool.stop()
        self.assertEqual(result, ["ok"])

    def test_stop_joins_threads(self):
        """stop() must clear thread list and not leave live workers."""
        pool = WorkerPool(workers=3, join_timeout=2.0)
        pool.start()
        self.assertEqual(len(pool.threads), 3)
        for t in pool.threads:
            self.assertTrue(t.is_alive())

        started = threading.Event()
        release = threading.Event()

        def blocker():
            started.set()
            release.wait(timeout=5.0)

        pool.submit(blocker)
        self.assertTrue(started.wait(timeout=2.0))
        release.set()
        pool.stop()

        self.assertFalse(pool.running)
        self.assertEqual(pool.threads, [])

    def test_restart_after_stop(self):
        pool = WorkerPool(workers=1, join_timeout=2.0)
        pool.start()
        out = []
        pool.submit(lambda: out.append(1))
        time.sleep(0.2)
        pool.stop()
        pool.start()
        pool.submit(lambda: out.append(2))
        time.sleep(0.2)
        pool.stop()
        self.assertEqual(out, [1, 2])

    def test_job_exception_does_not_kill_pool(self):
        pool = WorkerPool(workers=1, join_timeout=2.0)
        pool.start()
        ok = []

        def boom():
            raise RuntimeError("boom")

        pool.submit(boom)
        pool.submit(lambda: ok.append("ok"))
        time.sleep(0.4)
        pool.stop()
        self.assertEqual(ok, ["ok"])


if __name__ == "__main__":
    unittest.main()
