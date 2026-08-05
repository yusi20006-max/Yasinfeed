import unittest

from yasinfeed.api.version import API_VERSION, API_NAME

class TestApiVersion(unittest.TestCase):

    def test_constants(self):
        self.assertEqual(API_VERSION, "v1")
        self.assertEqual(API_NAME, "YasinFeed API")

if __name__ == "__main__":
    unittest.main()
