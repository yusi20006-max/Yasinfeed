import unittest
import time

from yasinfeed.worker import WorkerPool

class TestWorker(unittest.TestCase):

    def test_worker(self):
        result=[]

        pool=WorkerPool(1)
        pool.start()

        pool.submit(lambda: result.append("ok"))

        time.sleep(0.3)

        pool.stop()

        self.assertEqual(result,["ok"])

if __name__=="__main__":
    unittest.main()
