import unittest,os,tempfile
from yasinfeed.backup.backup import backup

class T(unittest.TestCase):
    def test_backup(self):
        f=tempfile.NamedTemporaryFile(delete=False)
        f.write(b"abc")
        f.close()
        dst=f.name+".bak"
        backup(f.name,dst)
        self.assertTrue(os.path.exists(dst))

if __name__=="__main__":
    unittest.main()
