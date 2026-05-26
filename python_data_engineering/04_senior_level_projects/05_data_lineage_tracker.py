"""Tiny lineage tracker for pipeline observability."""
from collections import defaultdict


class LineageTracker:
    def __init__(self) -> None:
        self.graph: dict[str, list[str]] = defaultdict(list)

    def record(self, source: str, target: str) -> None:
        self.graph[source].append(target)

    def upstream_of(self, target: str) -> list[str]:
        return [src for src, targets in self.graph.items() if target in targets]


def main() -> None:
    tracker = LineageTracker()
    tracker.record("raw.orders", "silver.orders")
    tracker.record("silver.orders", "gold.daily_sales")
    tracker.record("raw.customers", "silver.customers")
    print(tracker.upstream_of("gold.daily_sales"))
    print(tracker.upstream_of("silver.orders"))


if __name__ == "__main__":
    main()
