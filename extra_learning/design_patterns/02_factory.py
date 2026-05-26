"""Factory: return a concrete implementation based on a key."""
from __future__ import annotations
from typing import Protocol


class Notifier(Protocol):
    def send(self, msg: str) -> None: ...


class EmailNotifier:
    def send(self, msg: str) -> None: print("email:", msg)


class SMSNotifier:
    def send(self, msg: str) -> None: print("sms:", msg)


_REGISTRY: dict[str, type[Notifier]] = {"email": EmailNotifier, "sms": SMSNotifier}


def make_notifier(kind: str) -> Notifier:
    if kind not in _REGISTRY:
        raise ValueError(f"unknown notifier {kind!r}")
    return _REGISTRY[kind]()


if __name__ == "__main__":
    make_notifier("email").send("hi")
    make_notifier("sms").send("yo")
