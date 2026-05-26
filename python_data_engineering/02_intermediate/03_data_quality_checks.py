from collections import Counter


def validate_orders(rows: list[dict[str, object]]) -> list[str]:
    errors = []
    ids = [row.get("order_id") for row in rows]
    duplicates = [value for value, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate order IDs: {duplicates}")
    for index, row in enumerate(rows, start=1):
        if row.get("order_id") is None:
            errors.append(f"Row {index} missing order_id")
        if float(row.get("amount", 0)) < 0:
            errors.append(f"Row {index} has negative amount")
    return errors


def main() -> None:
    rows = [{"order_id": 1, "amount": 100}, {"order_id": 1, "amount": -10}, {"amount": 50}]
    for error in validate_orders(rows):
        print(error)


if __name__ == "__main__":
    main()
