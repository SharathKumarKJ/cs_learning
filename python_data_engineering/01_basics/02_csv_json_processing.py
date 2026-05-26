import csv
import json
from pathlib import Path


def csv_to_json(csv_file: Path, json_file: Path) -> None:
    with csv_file.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> None:
    input_file = Path("output/customers.csv")
    output_file = Path("output/customers.json")
    input_file.parent.mkdir(parents=True, exist_ok=True)
    input_file.write_text("id,name,city\n1,Asha,Bengaluru\n2,Ravi,Pune\n", encoding="utf-8")
    csv_to_json(input_file, output_file)
    print(output_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
