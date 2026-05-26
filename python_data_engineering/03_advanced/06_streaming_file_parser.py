"""Memory-efficient streaming parser for large files."""
from pathlib import Path
from typing import Iterator


def stream_csv_rows(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as source:
        header = source.readline().strip().split(",")
        for line in source:
            values = line.strip().split(",")
            yield dict(zip(header, values))


def main() -> None:
    path = Path("output/big.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("id,name\n1,Asha\n2,Ravi\n3,Meera\n", encoding="utf-8")
    for row in stream_csv_rows(path):
        print(row)


if __name__ == "__main__":
    main()
