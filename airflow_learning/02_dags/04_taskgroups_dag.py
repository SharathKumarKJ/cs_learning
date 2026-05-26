"""TaskGroups example."""
from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup


with DAG("taskgroup_example", start_date=datetime(2026, 1, 1), schedule=None, catchup=False) as dag:
    start = EmptyOperator(task_id="start")
    with TaskGroup("extract") as extract_group:
        EmptyOperator(task_id="from_db")
        EmptyOperator(task_id="from_api")
    with TaskGroup("load") as load_group:
        EmptyOperator(task_id="to_warehouse")
        EmptyOperator(task_id="to_lake")
    end = EmptyOperator(task_id="end")
    start >> extract_group >> load_group >> end
