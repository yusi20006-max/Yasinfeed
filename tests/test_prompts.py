import unittest
from yasinfeed.ai.prompts import PromptManager

class T(unittest.TestCase):
    def test_prompt(self):
        p=PromptManager()
        p.add("rewrite","hello")
        self.assertEqual(p.get("rewrite"),"hello")

if __name__=="__main__":
    unittest.main()
