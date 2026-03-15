from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def _transform(**context):
    print("Трансформация: очистка, применение бизнес-правил")
    return "transformed_data"


def _validate(**context):
    print("Валидация: проверка целостности данных")
    return True


with DAG(
    dag_id="etl_pipeline",
    description="ETL: extract -> transform -> validate -> load",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["final_assignment", "etl"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command='echo "Извлечение данных из источника..." && sleep 2',
    )

    transform = PythonOperator(task_id="transform", python_callable=_transform)
    validate = PythonOperator(task_id="validate", python_callable=_validate)

    load = BashOperator(
        task_id="load",
        bash_command='echo "Загрузка данных в хранилище..." && sleep 1',
    )

    extract >> transform >> validate >> load
