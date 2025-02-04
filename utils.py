from functools import wraps
import time


def timer(func):
    """helper function to estimate function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # record start time
        start = time.time()

        # func execution
        result = func(*args, **kwargs)

        duration = (time.time() - start)
        # output execution time to console
        print(f'function {func.__name__} takes {duration:.2f} s')
        return result

    return wrapper
