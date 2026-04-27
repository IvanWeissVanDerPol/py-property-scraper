"""HTTP client with rate limiting and retry logic."""

import random
import time
from functools import wraps

import httpx


def rate_limit(delay: float):
    """Decorator to enforce a minimum delay between requests."""
    last_call = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < delay:
                time.sleep(delay - elapsed + random.uniform(0, 0.5))
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper
    return decorator


def get_client(timeout: int = 30) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-PY,es;q=0.9,en;q=0.8",
        },
    )
