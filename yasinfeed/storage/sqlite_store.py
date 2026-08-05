import sqlite3

class SQLiteStore:

    def __init__(self,path="yasinfeed.db"):
        self.db=sqlite3.connect(path)

    def execute(self,sql,args=()):
        cur=self.db.cursor()
        cur.execute(sql,args)
        self.db.commit()
        return cur
