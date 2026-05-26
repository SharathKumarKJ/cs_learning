import logging
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def count_records(file_path: Path) -> int:
    try:
        return len(file_path.read_text(encoding="utf-8").splitlines())
    except FileNotFoundError:
        logging.error("File not found: %s", file_path)
        return 0
    except PermissionError:
        logging.error("Permission denied: %s", file_path)
        return 0


def main() -> None:
    total = count_records(Path("missing_file.csv"))
    logging.info("Total records: %s", total)


if __name__ == "__main__":
    main()
