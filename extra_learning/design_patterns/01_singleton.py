"""Singleton via a metaclass — thread-safe lazy initialization."""
from __future__ import annotations
import threading


class SingletonMeta(type):
    _instances: dict[type, object] = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    def __init__(self) -> None:
        print("init config (once)")
        self.env = "prod"


if __name__ == "__main__":
    a = Config()
    b = Config()
    print(a is b, a.env)
