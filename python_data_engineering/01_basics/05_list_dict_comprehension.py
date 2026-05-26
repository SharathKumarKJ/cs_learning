"""List and dict comprehensions common in data engineering."""


def main() -> None:
    rows = [{"id": 1, "amount": 100}, {"id": 2, "amount": 250}, {"id": 3, "amount": 80}]
    high_value_ids = [row["id"] for row in rows if row["amount"] >= 100]
    print(high_value_ids)
    amount_by_id = {row["id"]: row["amount"] for row in rows}
    print(amount_by_id)
    squared = {n: n * n for n in range(1, 6)}
    print(squared)


if __name__ == "__main__":
    main()
