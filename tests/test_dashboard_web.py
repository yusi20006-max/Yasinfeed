import unittest
from yasinfeed.dashboard.web import WebDashboard

class T(unittest.TestCase):
    def test_render(self):
        self.assertEqual(
            WebDashboard().render({"x":1})["dashboard"]["x"],1
        )

if __name__=="__main__":
    unittest.main()
