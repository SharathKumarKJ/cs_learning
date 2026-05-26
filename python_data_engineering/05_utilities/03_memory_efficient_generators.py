from collections.abc import Iterator


def batch_records(records: Iterator[int], batch_size: int) -> Iterator[list[int]]:
    batch = []
    for record in records:
        batch.append(record)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> None:
    records = (number for number in range(1, 11))
    for batch in batch_records(records, 3):
        print(batch)


if __name__ == "__main__":
    main()
