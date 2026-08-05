import hashlib

class Deduplicator:
    def __init__(self):
        self.seen=set()

    def add(self,text):
        h=hashlib.sha256(text.encode()).hexdigest()
        if h in self.seen:
            return False
        self.seen.add(h)
        return True
