"""Chain of responsibility / middleware."""
from __future__ import annotations
from collections.abc import Callable


def auth(next_: Callable[[str], None]) -> Callable[[str], None]:
    def inner(req: str) -> None:
        print("auth ok"); next_(req)
    return inner


def log_(next_: Callable[[str], None]) -> Callable[[str], None]:
    def inner(req: str) -> None:
        print("log:", req); next_(req)
    return inner


def handler(req: str) -> None:
    print("handler:", req)


if __name__ == "__main__":
    pipeline = log_(auth(handler))
    pipeline("hello")
