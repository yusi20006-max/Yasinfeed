import unittest

from yasinfeed.auth import APIKeyAuth


class TestAuth(unittest.TestCase):

    def test_api_key(self):
        auth = APIKeyAuth("secret")

        self.assertTrue(auth.verify("secret"))
        self.assertFalse(auth.verify("wrong"))


if __name__ == "__main__":
    unittest.main()
