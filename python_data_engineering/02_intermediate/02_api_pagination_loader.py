from collections.abc import Callable


PageFetcher = Callable[[int], list[dict[str, object]]]


def fetch_all_pages(fetch_page: PageFetcher) -> list[dict[str, object]]:
    page_number = 1
    records = []
    while True:
        page = fetch_page(page_number)
        if not page:
            break
        records.extend(page)
        page_number += 1
    return records


def fake_api(page_number: int) -> list[dict[str, object]]:
    pages = {
        1: [{"id": 1, "status": "created"}, {"id": 2, "status": "paid"}],
        2: [{"id": 3, "status": "shipped"}],
    }
    return pages.get(page_number, [])


def main() -> None:
    for record in fetch_all_pages(fake_api):
        print(record)


if __name__ == "__main__":
    main()
