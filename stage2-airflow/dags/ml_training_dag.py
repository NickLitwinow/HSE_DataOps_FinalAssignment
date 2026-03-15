from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def _prepare_data(**context):
    print("Загрузка обучающей выборки, split 80/20")
    return {"train_size": 800, "test_size": 200}


def _evaluate_model(**context):
    metrics = {"rmse": 53.47, "mae": 43.21, "r2": 0.48}
    print(f"Метрики: {metrics}")
    return metrics


with DAG(
    dag_id="ml_training_pipeline",
    description="Пайплайн обучения: данные -> обучение -> оценка -> регистрация",
    start_date=datetime(2025, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["final_assignment", "ml"],
) as dag:

    prepare = PythonOperator(task_id="prepare_data", python_callable=_prepare_data)

    train = BashOperator(
        task_id="train_model",
        bash_command='echo "Обучение Ridge Regression..." && sleep 3',
    )

    evaluate = PythonOperator(task_id="evaluate_model", python_callable=_evaluate_model)

    register = BashOperator(
        task_id="register_model",
        bash_command='echo "Регистрация модели..." && sleep 1',
    )

    prepare >> train >> evaluate >> register
