"""Async concurrent fetching pattern (uses asyncio + simulated work)."""
import asyncio


async def fetch_record(record_id: int) -> dict:
    await asyncio.sleep(0.1)
    return {"id": record_id, "status": "ok"}


async def fetch_many(ids: list[int]) -> list[dict]:
    return await asyncio.gather(*(fetch_record(i) for i in ids))


def main() -> None:
    results = asyncio.run(fetch_many(list(range(1, 6))))
    for record in results:
        print(record)


if __name__ == "__main__":
    main()
