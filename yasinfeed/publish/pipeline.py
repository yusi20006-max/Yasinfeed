class PublishPipeline:
    def __init__(self):
        self.targets=[]
    def register(self,t):
        self.targets.append(t)
    def publish(self,article):
        for t in self.targets:
            t.publish(article)
