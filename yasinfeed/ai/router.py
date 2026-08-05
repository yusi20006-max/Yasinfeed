class AIRouter:
    def __init__(self):
        self.providers=[]

    def register(self,p):
        self.providers.append(p)

    def rewrite(self,text):
        for p in self.providers:
            try:
                return p.rewrite(text)
            except Exception:
                pass
        return text
