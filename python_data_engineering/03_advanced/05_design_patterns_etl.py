"""Strategy + Factory pattern for ETL transformations."""
from abc import ABC, abstractmethod


class Transformer(ABC):
    @abstractmethod
    def apply(self, row: dict) -> dict: ...


class UppercaseName(Transformer):
    def apply(self, row: dict) -> dict:
        row["name"] = row["name"].upper()
        return row


class HighValueFlag(Transformer):
    def apply(self, row: dict) -> dict:
        row["is_high_value"] = row["amount"] >= 1000
        return row


def get_transformer(name: str) -> Transformer:
    registry = {"uppercase_name": UppercaseName(), "high_value_flag": HighValueFlag()}
    return registry[name]


def main() -> None:
    row = {"name": "asha", "amount": 1500}
    for step in ["uppercase_name", "high_value_flag"]:
        row = get_transformer(step).apply(row)
    print(row)


if __name__ == "__main__":
    main()
