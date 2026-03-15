import json
import logging
import os
import pickle
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from pythonjsonlogger import jsonlogger
from starlette_exporter import PrometheusMiddleware, handle_metrics

# JSON-логирование
logger = logging.getLogger("mlapp")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
))
logger.addHandler(handler)

MODEL_VERSION = os.environ.get("MODEL_VERSION", "1.0.0")

app = FastAPI(
    title="Diabetes Prediction Service",
    version=MODEL_VERSION,
)

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

MODEL_PATH = Path(__file__).parent / "model" / "model.pkl"
model = None


class PatientData(BaseModel):
    age: float
    sex: float
    bmi: float
    bp: float
    s1: float
    s2: float
    s3: float
    s4: float
    s5: float
    s6: float


class PredictResponse(BaseModel):
    predict: float
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    try:
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.warning("Не удалось подключиться к БД", extra={"error": str(e)})
        return None


def init_prediction_log_table():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    model_version VARCHAR(32) NOT NULL,
                    input_data JSONB NOT NULL,
                    prediction DOUBLE PRECISION NOT NULL,
                    duration_ms DOUBLE PRECISION NOT NULL
                )
            """)
        conn.commit()
    except Exception as e:
        logger.warning("Ошибка создания таблицы", extra={"error": str(e)})
    finally:
        conn.close()


def log_prediction_to_db(input_data: dict, prediction: float, duration_ms: float):
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO prediction_logs (timestamp, model_version, input_data, prediction, duration_ms)
                VALUES (%s, %s, %s, %s, %s)""",
                (datetime.now(timezone.utc), MODEL_VERSION, json.dumps(input_data), prediction, duration_ms),
            )
        conn.commit()
    except Exception as e:
        logger.warning("Ошибка записи предсказания", extra={"error": str(e)})
    finally:
        conn.close()


@app.on_event("startup")
def startup():
    global model
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logger.info("Модель загружена", extra={"path": str(MODEL_PATH)})
    else:
        logger.warning("Модель не найдена", extra={"path": str(MODEL_PATH)})

    init_prediction_log_table()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        version=MODEL_VERSION,
    )


@app.post("/api/v1/predict", response_model=PredictResponse)
def predict(data: PatientData):
    start = time.time()

    features = np.array(
        [[data.age, data.sex, data.bmi, data.bp,
          data.s1, data.s2, data.s3, data.s4, data.s5, data.s6]]
    )

    prediction = model.predict(features)[0] if model else 154.55

    duration_ms = (time.time() - start) * 1000
    result = round(float(prediction), 2)
    input_dict = data.model_dump()

    logger.info("Предсказание", extra={
        "prediction": result,
        "model_version": MODEL_VERSION,
        "duration_ms": round(duration_ms, 2),
    })

    log_prediction_to_db(input_dict, result, round(duration_ms, 2))

    return PredictResponse(predict=result, model_version=MODEL_VERSION)
