import unittest
from yasinfeed.storage.sqlite_store import SQLiteStore

class T(unittest.TestCase):
    def test_db(self):
        db=SQLiteStore(":memory:")
        db.execute("create table t(id integer)")
        db.execute("insert into t values(1)")
        c=db.execute("select count(*) from t")
        self.assertEqual(c.fetchone()[0],1)

if __name__=="__main__":
    unittest.main()
