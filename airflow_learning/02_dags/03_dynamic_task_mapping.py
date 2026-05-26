"""Dynamic task mapping example."""
from datetime import datetime
from airflow.decorators import dag, task


@dag(dag_id="dynamic_task_mapping", start_date=datetime(2026, 1, 1), schedule=None, catchup=False)
def dynamic_mapping():
    @task
    def list_files() -> list[str]:
        return ["file_a.csv", "file_b.csv", "file_c.csv"]

    @task
    def process(file_name: str) -> str:
        return f"processed:{file_name}"

    process.expand(file_name=list_files())


dynamic_mapping()
