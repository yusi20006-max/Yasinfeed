from queue import Queue

class FeedQueue:

    def __init__(self):
        self.q=Queue()

    def push(self,item):
        self.q.put(item)

    def pop(self):
        return self.q.get()

    def size(self):
        return self.q.qsize()
