import json
from collections import defaultdict
from pathlib import Path


def write_partitioned_json(records: list[dict[str, object]], base_path: Path, partition_column: str) -> None:
    grouped: dict[object, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[record[partition_column]].append(record)
    for partition_value, rows in grouped.items():
        partition_path = base_path / f"{partition_column}={partition_value}"
        partition_path.mkdir(parents=True, exist_ok=True)
        (partition_path / "data.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> None:
    orders = [{"id": 1, "order_date": "2026-01-01"}, {"id": 2, "order_date": "2026-01-02"}, {"id": 3, "order_date": "2026-01-01"}]
    write_partitioned_json(orders, Path("output/orders_lake"), "order_date")
    print("Partitioned data written to output/orders_lake")


if __name__ == "__main__":
    main()
