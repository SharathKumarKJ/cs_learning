def detect_schema_drift(expected: dict[str, type], actual_row: dict[str, object]) -> list[str]:
    issues = []
    for column, expected_type in expected.items():
        if column not in actual_row:
            issues.append(f"Missing column: {column}")
        elif not isinstance(actual_row[column], expected_type):
            issues.append(f"Type mismatch for {column}: expected {expected_type.__name__}")
    for column in actual_row:
        if column not in expected:
            issues.append(f"Unexpected column: {column}")
    return issues


def main() -> None:
    expected_schema = {"id": int, "name": str, "amount": float}
    actual = {"id": "1", "name": "Asha", "country": "IN"}
    for issue in detect_schema_drift(expected_schema, actual):
        print(issue)


if __name__ == "__main__":
    main()
