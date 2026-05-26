"""Observer / pub-sub using a simple in-process bus."""
from __future__ import annotations
from collections import defaultdict
from collections.abc import Callable


class Bus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable[[str], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[str], None]) -> None:
        self._subs[topic].append(handler)

    def publish(self, topic: str, msg: str) -> None:
        for h in self._subs[topic]:
            h(msg)


if __name__ == "__main__":
    bus = Bus()
    bus.subscribe("orders", lambda m: print("audit:", m))
    bus.subscribe("orders", lambda m: print("metrics:", m))
    bus.publish("orders", "order-1")
