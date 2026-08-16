import unittest
from yasinfeed.retry import retry


class TestRetry(unittest.TestCase):
    def test_retry(self):
        c = {"n": 0}

        def f():
            c["n"] += 1
            if c["n"] < 3:
                raise Exception("fail")
            return "ok"

        self.assertEqual(retry(f, delay=0.01, backoff=1.5), "ok")
        self.assertEqual(c["n"], 3)

    def test_retry_exhausts(self):
        def always_fail():
            raise ValueError("x")

        with self.assertRaises(ValueError):
            retry(always_fail, retries=2, delay=0.01, backoff=1.0)

    def test_retries_validation(self):
        with self.assertRaises(ValueError):
            retry(lambda: 1, retries=0)


if __name__ == "__main__":
    unittest.main()
