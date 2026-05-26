"""Retry with exponential backoff and jitter."""
from __future__ import annotations
import random
import time
from collections.abc import Callable


def retry(fn: Callable[[], object], attempts: int = 4, base: float = 0.1) -> object:
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_err = e
            sleep_for = base * (2 ** i)
            sleep_for += random.uniform(0, sleep_for / 4)
            time.sleep(sleep_for)
    raise RuntimeError(f"after {attempts} attempts") from last_err


if __name__ == "__main__":
    counter = {"n": 0}

    def flaky() -> str:
        counter["n"] += 1
        if counter["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    print(retry(flaky))
