class Metrics:

    def __init__(self):
        self._data = {}

    def inc(self, name, value=1):
        self._data[name] = self._data.get(name, 0) + value

    def set(self, name, value):
        self._data[name] = value

    def get(self, name):
        return self._data.get(name)

    def all(self):
        return dict(self._data)
