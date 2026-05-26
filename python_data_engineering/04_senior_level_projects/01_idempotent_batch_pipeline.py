import hashlib
import json
from pathlib import Path


def record_hash(record: dict[str, object]) -> str:
    payload = json.dumps(record, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def process_batch(records: list[dict[str, object]], processed_hashes: set[str]) -> list[dict[str, object]]:
    output = []
    for record in records:
        fingerprint = record_hash(record)
        if fingerprint not in processed_hashes:
            output.append(record | {"record_hash": fingerprint})
            processed_hashes.add(fingerprint)
    return output


def main() -> None:
    target = Path("output/idempotent_batch.json")
    processed: set[str] = set()
    batch = [{"id": 1, "amount": 100}, {"id": 1, "amount": 100}, {"id": 2, "amount": 200}]
    result = process_batch(batch, processed)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
