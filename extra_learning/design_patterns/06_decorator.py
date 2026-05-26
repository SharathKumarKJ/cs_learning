"""Decorator: wrap callables to add behavior."""
from __future__ import annotations
import time
from collections.abc import Callable
from functools import wraps


def with_logging(fn: Callable) -> Callable:
    @wraps(fn)
    def inner(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        print(f"{fn.__name__} took {(time.perf_counter()-start)*1000:.2f} ms")
        return result
    return inner


def with_cache(fn: Callable) -> Callable:
    cache: dict[tuple, object] = {}

    @wraps(fn)
    def inner(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]
    return inner


@with_logging
@with_cache
def slow_double(x: int) -> int:
    time.sleep(0.05)
    return x * 2


if __name__ == "__main__":
    print(slow_double(5))
    print(slow_double(5))
