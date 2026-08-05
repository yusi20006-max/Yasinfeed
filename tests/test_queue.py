import unittest
from yasinfeed.queue import FeedQueue

class TestQueue(unittest.TestCase):

    def test_queue(self):
        q=FeedQueue()

        q.push("a")
        q.push("b")

        self.assertEqual(q.size(),2)
        self.assertEqual(q.pop(),"a")

if __name__=="__main__":
    unittest.main()
