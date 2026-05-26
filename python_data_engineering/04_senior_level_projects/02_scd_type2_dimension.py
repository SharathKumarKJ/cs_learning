from datetime import date


def apply_scd_type2(current_rows: list[dict[str, object]], changes: list[dict[str, object]], effective_date: date) -> list[dict[str, object]]:
    result = [row.copy() for row in current_rows]
    active_by_key = {row["customer_id"]: row for row in result if row["is_current"]}
    for change in changes:
        existing = active_by_key.get(change["customer_id"])
        if existing and existing["city"] != change["city"]:
            existing["valid_to"] = effective_date.isoformat()
            existing["is_current"] = False
            result.append(change | {"valid_from": effective_date.isoformat(), "valid_to": None, "is_current": True})
        elif not existing:
            result.append(change | {"valid_from": effective_date.isoformat(), "valid_to": None, "is_current": True})
    return result


def main() -> None:
    current = [{"customer_id": 1, "name": "Asha", "city": "Pune", "valid_from": "2026-01-01", "valid_to": None, "is_current": True}]
    changes = [{"customer_id": 1, "name": "Asha", "city": "Bengaluru"}, {"customer_id": 2, "name": "Ravi", "city": "Delhi"}]
    for row in apply_scd_type2(current, changes, date(2026, 2, 1)):
        print(row)


if __name__ == "__main__":
    main()
