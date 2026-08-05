import os
import unittest

class TestDeployment(unittest.TestCase):

    def test_files_exist(self):
        self.assertTrue(os.path.exists("scripts/run.sh"))
        self.assertTrue(os.path.exists("scripts/test.sh"))
        self.assertTrue(os.path.exists(".github/workflows/python.yml"))
        self.assertTrue(os.path.exists("deploy/README.md"))

if __name__ == "__main__":
    unittest.main()
