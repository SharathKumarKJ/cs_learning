import json
from pathlib import Path


def load_config(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = Path("output/config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('{"source":"s3","retries":3,"batch_size":1000}', encoding="utf-8")
    config = load_config(config_path)
    print(config["source"], config["retries"], config["batch_size"])


if __name__ == "__main__":
    main()
