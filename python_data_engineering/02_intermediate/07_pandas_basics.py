"""Pandas basics for data engineering. Requires pandas installed."""
try:
    import pandas as pd
except ImportError:
    pd = None


def main() -> None:
    if pd is None:
        print("Install pandas: pip install pandas")
        return
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Asha", "Ravi", "Meera"], "amount": [100, 250, 80]})
    print(df.describe())
    print(df[df["amount"] > 90])
    print(df.groupby("name")["amount"].sum())


if __name__ == "__main__":
    main()
