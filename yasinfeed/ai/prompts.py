class PromptManager:

    def __init__(self):
        self.prompts={}

    def add(self,name,text):
        self.prompts[name]=text

    def get(self,name):
        return self.prompts.get(name,"")
