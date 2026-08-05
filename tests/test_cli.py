import unittest
import subprocess
import sys

class TestCLI(unittest.TestCase):

    def test_version(self):
        r = subprocess.run(
            [sys.executable, "-m", "yasinfeed.cli.main", "version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("v0.1", r.stdout)

if __name__ == "__main__":
    unittest.main()
