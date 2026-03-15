"""Обучение моделей на датасете Diabetes с логированием в MLflow."""

import os
import pickle
from pathlib import Path

import mlflow
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


MLFLOW_TRACKING_URI = "http://localhost:5001"
EXPERIMENT_NAME = "diabetes-prediction"

os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "minio_admin")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minio_secret123")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_NAME)


def evaluate(model, X_test, y_test):
    preds = model.predict(X_test)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
        "mae": float(mean_absolute_error(y_test, preds)),
        "r2": float(r2_score(y_test, preds)),
    }


def train_and_log(model, name, X_train, X_test, y_train, y_test, params=None):
    with mlflow.start_run(run_name=name):
        mlflow.log_param("model_type", name)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        mlflow.log_param("n_features", X_train.shape[1])
        if params:
            mlflow.log_params(params)

        model.fit(X_train, y_train)
        metrics = evaluate(model, X_test, y_test)
        mlflow.log_metrics(metrics)

        model_path = Path(f"/tmp/{name}_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        mlflow.log_artifact(str(model_path), artifact_path="model")

        print(f"  {name}: RMSE={metrics['rmse']:.2f}, MAE={metrics['mae']:.2f}, R2={metrics['r2']:.4f}")

    return metrics


def main():
    data = load_diabetes()
    X_train, X_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )

    print(f"Датасет: {len(data.data)} записей, {len(data.feature_names)} признаков")
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    print()

    models = [
        (LinearRegression(), "LinearRegression", None),
        (Ridge(alpha=1.0), "Ridge_alpha_1.0", {"alpha": 1.0}),
        (Ridge(alpha=0.5), "Ridge_alpha_0.5", {"alpha": 0.5}),
        (Lasso(alpha=0.1), "Lasso_alpha_0.1", {"alpha": 0.1}),
    ]

    print("Обучение моделей:")
    for model, name, params in models:
        train_and_log(model, name, X_train, X_test, y_train, y_test, params)

    print()
    print(f"Результаты в MLflow: {MLFLOW_TRACKING_URI}")


if __name__ == "__main__":
    main()
