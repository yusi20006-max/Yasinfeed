class Metrics:

    def __init__(self):
        self.data={}

    def set(self,k,v):
        self.data[k]=v

    def all(self):
        return self.data
