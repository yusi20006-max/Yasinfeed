import secrets

class APIKeyManager:

    def __init__(self):
        self._keys = set()

    def generate(self):
        key = secrets.token_hex(32)
        self._keys.add(key)
        return key

    def validate(self, key):
        return key in self._keys

    def revoke(self, key):
        self._keys.discard(key)
