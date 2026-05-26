"""Database connection example with sqlite3."""
import sqlite3
from pathlib import Path


def setup_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT)")
        conn.executemany("INSERT OR REPLACE INTO customers VALUES (?, ?, ?)", [(1, "Asha", "Pune"), (2, "Ravi", "Delhi")])


def fetch_customers(db_path: Path) -> list[tuple]:
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT id, name, city FROM customers").fetchall()


def main() -> None:
    db = Path("output/sample.db")
    setup_database(db)
    for row in fetch_customers(db):
        print(row)


if __name__ == "__main__":
    main()
