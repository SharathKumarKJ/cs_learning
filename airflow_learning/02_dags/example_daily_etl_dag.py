from datetime import datetime

from airflow.decorators import dag, task


@dag(dag_id="example_daily_etl", start_date=datetime(2026, 1, 1), schedule="@daily", catchup=False, tags=["learning"])
def example_daily_etl():
    @task
    def extract() -> list[dict[str, object]]:
        return [{"order_id": 1, "amount": 100}, {"order_id": 2, "amount": 250}]

    @task
    def transform(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [row | {"is_high_value": row["amount"] >= 200} for row in rows]

    @task
    def load(rows: list[dict[str, object]]) -> int:
        print(rows)
        return len(rows)

    load(transform(extract()))


example_daily_etl()
