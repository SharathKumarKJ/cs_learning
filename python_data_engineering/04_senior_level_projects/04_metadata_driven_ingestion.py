"""Metadata-driven ingestion framework skeleton."""
from dataclasses import dataclass
from typing import Callable


@dataclass
class SourceConfig:
    name: str
    load_type: str  # full | incremental
    primary_key: str
    watermark_column: str | None = None


def ingest(config: SourceConfig, extractor: Callable[[SourceConfig], list[dict]]) -> list[dict]:
    rows = extractor(config)
    if config.load_type == "incremental" and config.watermark_column:
        rows = sorted(rows, key=lambda r: r[config.watermark_column])
    return rows


def fake_extract(config: SourceConfig) -> list[dict]:
    return [{"id": 1, "updated_at": "2026-01-01"}, {"id": 2, "updated_at": "2026-01-03"}]


def main() -> None:
    cfg = SourceConfig(name="orders", load_type="incremental", primary_key="id", watermark_column="updated_at")
    print(ingest(cfg, fake_extract))


if __name__ == "__main__":
    main()
