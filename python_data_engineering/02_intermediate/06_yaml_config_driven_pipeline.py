"""Config-driven processing using a small DSL-like dict (yaml-compatible)."""
from pathlib import Path
import json


def run_pipeline(config: dict) -> list[dict]:
    rows = [{"id": 1, "amount": 50}, {"id": 2, "amount": 500}, {"id": 3, "amount": 1500}]
    if "filter_min_amount" in config:
        rows = [r for r in rows if r["amount"] >= config["filter_min_amount"]]
    if config.get("add_tier"):
        for r in rows:
            r["tier"] = "HIGH" if r["amount"] >= 1000 else "LOW"
    return rows


def main() -> None:
    config = {"filter_min_amount": 100, "add_tier": True}
    output = run_pipeline(config)
    Path("output").mkdir(exist_ok=True)
    Path("output/pipeline_result.json").write_text(json.dumps(output, indent=2))
    print(output)


if __name__ == "__main__":
    main()
