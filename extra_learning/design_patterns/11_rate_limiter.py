"""Token-bucket rate limiter."""
from __future__ import annotations
import time


class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: float) -> None:
        self.rate = rate_per_sec; self.capacity = capacity
        self.tokens = capacity; self.last = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


if __name__ == "__main__":
    b = TokenBucket(2, 5)
    for i in range(8):
        print(i, b.allow())
        time.sleep(0.1)
