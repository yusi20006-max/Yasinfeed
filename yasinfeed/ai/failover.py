class FailoverProvider:
    def __init__(self,*providers):
        self.providers=providers

    def rewrite(self,text):
        for p in self.providers:
            try:
                return p.rewrite(text)
            except Exception:
                continue
        return text
