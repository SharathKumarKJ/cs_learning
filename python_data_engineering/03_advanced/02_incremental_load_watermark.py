from datetime import datetime


def incremental_records(records: list[dict[str, str]], last_watermark: str) -> list[dict[str, str]]:
    watermark = datetime.fromisoformat(last_watermark)
    return [row for row in records if datetime.fromisoformat(row["updated_at"]) > watermark]


def main() -> None:
    source = [
        {"id": "1", "updated_at": "2026-01-01T10:00:00"},
        {"id": "2", "updated_at": "2026-01-02T10:00:00"},
        {"id": "3", "updated_at": "2026-01-03T10:00:00"},
    ]
    for record in incremental_records(source, "2026-01-02T00:00:00"):
        print(record)


if __name__ == "__main__":
    main()
