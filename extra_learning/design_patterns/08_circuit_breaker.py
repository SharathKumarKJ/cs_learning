"""Circuit breaker."""
from __future__ import annotations
import time
from collections.abc import Callable
from enum import Enum, auto


class State(Enum):
    CLOSED = auto(); OPEN = auto(); HALF_OPEN = auto()


class CircuitOpen(Exception): pass


class Breaker:
    def __init__(self, threshold: int = 3, open_seconds: float = 1.0) -> None:
        self.threshold = threshold
        self.open_seconds = open_seconds
        self.state = State.CLOSED
        self.failures = 0
        self.opened_at = 0.0

    def call(self, fn: Callable[[], object]) -> object:
        if self.state == State.OPEN:
            if time.time() - self.opened_at > self.open_seconds:
                self.state = State.HALF_OPEN
            else:
                raise CircuitOpen
        try:
            result = fn()
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = State.OPEN
                self.opened_at = time.time()
            raise
        self.failures = 0
        self.state = State.CLOSED
        return result


if __name__ == "__main__":
    b = Breaker(threshold=2, open_seconds=0.5)
    for i in range(5):
        try:
            b.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except Exception as e:
            print(i, type(e).__name__)
        time.sleep(0.1)
