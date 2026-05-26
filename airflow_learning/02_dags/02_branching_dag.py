"""Branching DAG with BranchPythonOperator."""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator


def choose_branch(**_) -> str:
    import random
    return "process_high" if random.random() > 0.5 else "process_low"


with DAG("branching_example", start_date=datetime(2026, 1, 1), schedule=None, catchup=False) as dag:
    start = EmptyOperator(task_id="start")
    branch = BranchPythonOperator(task_id="branch", python_callable=choose_branch)
    high = EmptyOperator(task_id="process_high")
    low = EmptyOperator(task_id="process_low")
    done = EmptyOperator(task_id="done", trigger_rule="none_failed_min_one_success")
    start >> branch >> [high, low] >> done
