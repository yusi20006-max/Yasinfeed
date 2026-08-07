import secrets


class APIKeyAuth:

    def __init__(self, secret=None):
        self.secret = secret
        self._keys = set()

        if secret:
            self._keys.add(secret)


    def generate(self):
        key = secrets.token_hex(32)
        self._keys.add(key)
        return key


    def validate(self, key):
        return key in self._keys


    def verify(self, key):
        return self.validate(key)


    def revoke(self, key):
        self._keys.discard(key)
