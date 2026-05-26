from pathlib import Path


def write_lines(file_path: Path, lines: list[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("\n".join(lines), encoding="utf-8")


def read_lines(file_path: Path) -> list[str]:
    return file_path.read_text(encoding="utf-8").splitlines()


def main() -> None:
    output_file = Path("output/sample_lines.txt")
    lines = ["customer_id,name", "1,Asha", "2,Ravi", "3,Meera"]
    write_lines(output_file, lines)
    for line in read_lines(output_file):
        print(line)


if __name__ == "__main__":
    main()
