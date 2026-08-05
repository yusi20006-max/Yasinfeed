class Cache:
    def __init__(self):
        self.data={}
    def set(self,k,v):
        self.data[k]=v
    def get(self,k,d=None):
        return self.data.get(k,d)
