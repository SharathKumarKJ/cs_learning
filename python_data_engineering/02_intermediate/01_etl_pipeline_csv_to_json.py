import csv
import json
from pathlib import Path


def extract(file_path: Path) -> list[dict[str, str]]:
    with file_path.open("r", encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def transform(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    result = []
    for row in rows:
        amount = float(row["amount"])
        result.append({"order_id": int(row["order_id"]), "customer": row["customer"], "amount": amount, "is_high_value": amount >= 1000})
    return result


def load(rows: list[dict[str, object]], file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> None:
    source = Path("output/orders.csv")
    target = Path("output/orders_curated.json")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("order_id,customer,amount\n1,Asha,1200\n2,Ravi,400\n", encoding="utf-8")
    load(transform(extract(source)), target)
    print(target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
