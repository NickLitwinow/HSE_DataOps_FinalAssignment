import json
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

ML_SERVICE_URL = "http://host.docker.internal:8000"


def _check_health(**context):
    import urllib.request

    req = urllib.request.Request(f"{ML_SERVICE_URL}/health")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    print(f"status={data['status']}, model_loaded={data['model_loaded']}, version={data['version']}")

    if data["status"] != "ok" or not data["model_loaded"]:
        raise ValueError("ML-сервис не готов!")

    return data


def _test_prediction(**context):
    import urllib.request

    payload = json.dumps({
        "age": 0.05, "sex": 0.05, "bmi": 0.06, "bp": 0.02,
        "s1": -0.04, "s2": -0.03, "s3": -0.04, "s4": 0.03,
        "s5": 0.04, "s6": -0.01,
    }).encode()

    req = urllib.request.Request(
        f"{ML_SERVICE_URL}/api/v1/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())

    print(f"prediction={result['predict']}, model_version={result['model_version']}")
    return result


def _log_result(**context):
    ti = context["ti"]
    health = ti.xcom_pull(task_ids="check_health")
    prediction = ti.xcom_pull(task_ids="test_prediction")

    report = {
        "timestamp": datetime.now().isoformat(),
        "status": health["status"],
        "version": health["version"],
        "test_prediction": prediction["predict"],
    }
    print(json.dumps(report, ensure_ascii=False))


with DAG(
    dag_id="ml_service_health_check",
    description="Проверка здоровья ML-сервиса",
    start_date=datetime(2025, 1, 1),
    schedule="@hourly",
    catchup=False,
    tags=["final_assignment", "ml", "monitoring"],
) as dag:

    check_health = PythonOperator(task_id="check_health", python_callable=_check_health)
    test_prediction = PythonOperator(task_id="test_prediction", python_callable=_test_prediction)
    log_result = PythonOperator(task_id="log_result", python_callable=_log_result)
    notify = BashOperator(task_id="notify_success", bash_command='echo "OK: $(date)"')

    check_health >> test_prediction >> log_result >> notify
