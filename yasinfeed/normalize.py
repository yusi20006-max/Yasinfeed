import re

def normalize(text):
    text=re.sub(r"\s+"," ",text)
    return text.strip()
