import time

def retry(fn, retries=3, delay=1, backoff=2):
    """
    Retry wrapper with exponential backoff.
    """
    for i in range(retries):
        try:
            return fn()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(delay * (backoff ** i))
