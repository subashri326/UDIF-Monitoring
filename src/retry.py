import time

def retry(func, retries=3, delay=2, backoff=2):
    def wrapper(*args, **kwargs):
        current_delay = delay

        for attempt in range(1, retries + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                print(f"Retry {attempt}/{retries} failed: {e}")

                if attempt == retries:
                    raise

                time.sleep(current_delay)
                current_delay *= backoff

    return wrapper