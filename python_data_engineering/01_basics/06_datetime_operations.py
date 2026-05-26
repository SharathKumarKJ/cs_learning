"""Date and time operations for data pipelines."""
from datetime import datetime, timedelta, timezone


def to_utc(local_time: datetime) -> datetime:
    return local_time.astimezone(timezone.utc)


def date_range(start: str, end: str) -> list[str]:
    start_date = datetime.fromisoformat(start).date()
    end_date = datetime.fromisoformat(end).date()
    days = (end_date - start_date).days
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range(days + 1)]


def main() -> None:
    print(to_utc(datetime.now().astimezone()))
    print(date_range("2026-01-01", "2026-01-05"))


if __name__ == "__main__":
    main()
