import urllib.request
import urllib.parse


class EitaaPublisher:
    def __init__(self, token, channel):
        self.token = token
        self.channel = channel

    def send(self, text):
        url = f"https://eitaayar.ir/api/{self.token}/sendMessage"

        data = urllib.parse.urlencode({
            "chat_id": self.channel,
            "text": text
        }).encode()

        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode()

        except Exception as e:
            print("Eitaa error:", e)
            return None
