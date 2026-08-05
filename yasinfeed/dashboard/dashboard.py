class Dashboard:

    def __init__(self, metrics):
        self.metrics = metrics

    def summary(self):
        return {
            "status": "ok",
            "metrics": self.metrics.all()
        }
