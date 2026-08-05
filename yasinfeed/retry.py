import time

def retry(fn,retries=3,delay=1):
    for i in range(retries):
        try:
            return fn()
        except Exception:
            if i==retries-1:
                raise
            time.sleep(delay)
