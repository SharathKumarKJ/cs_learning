from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def count_lines(file_path: Path) -> tuple[str, int]:
    return file_path.name, len(file_path.read_text(encoding="utf-8").splitlines())


def main() -> None:
    folder = Path("output/parallel_files")
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(1, 4):
        (folder / f"file_{index}.txt").write_text("a\nb\nc\n", encoding="utf-8")
    files = list(folder.glob("*.txt"))
    with ThreadPoolExecutor(max_workers=3) as executor:
        for file_name, total in executor.map(count_lines, files):
            print(file_name, total)


if __name__ == "__main__":
    main()
