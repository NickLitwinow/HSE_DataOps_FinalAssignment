# Итоговое задание — DataOps

Полный цикл сборки и развёртывания ML-сервиса: от поднятия ключевых компонентов
(MLflow, Airflow, LakeFS, JupyterHub) и регистрации артефактов до подготовки
сервиса к деплою в Kubernetes с использованием Helm Charts.

## Структура проекта

```
.
├── stage1-mlflow/           # MLflow Tracking Server
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── .env
│   └── research/
│       └── train_model.py   # Обучение моделей с логированием в MLflow
├── stage2-airflow/          # Apache Airflow
│   ├── docker-compose.yaml
│   ├── .env
│   └── dags/
│       ├── etl_pipeline_dag.py
│       ├── ml_training_dag.py
│       └── ml_service_health_dag.py
├── stage3-lakefs/           # LakeFS — версионирование данных
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   └── .env
├── stage4-jupyterhub/       # JupyterHub
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── jupyterhub_config.py
│   └── .env
├── stage5-ml-service/       # ML-сервис (FastAPI)
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── requirements.txt
│   ├── .env
│   └── mlapp/
│       ├── server.py        # FastAPI приложение
│       ├── __main__.py
│       └── model/model.pkl  # Обученная модель
├── stage6-monitoring/       # Prometheus + Grafana
│   ├── docker-compose.yaml
│   ├── .env
│   └── configs/
│       ├── prometheus.yml
│       └── grafana/         # Авто-провизионинг дашбордов
├── stage7-kubernetes/       # Kubernetes-манифесты
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── hpa.yaml
├── stage8-helm/             # Helm chart
│   └── ml-service-chart/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── templates/
│       └── examples/        # Production и Staging конфигурации
├── stage9-prompts/          # MLflow Prompt Storage
│   └── register_prompts.py
├── scripts/
│   └── smoke_test.sh        # Smoke-тест эндпоинтов
└── Makefile                 # Управление всеми сервисами
```

## Быстрый старт

Все сервисы можно запустить одновременно одной командой:

```bash
make all.up          # Запуск всех сервисов
make status          # Проверка статуса контейнеров
make all.down        # Остановка всех сервисов
```

Каждый этап также можно запускать по отдельности (см. ниже).

## Этап 1. MLflow

Развёрнут MLflow Tracking Server для отслеживания экспериментов и хранения артефактов.
Стек состоит из трёх компонентов: PostgreSQL 17 для хранения метаданных,
MinIO в качестве S3-совместимого хранилища артефактов и непосредственно MLflow Server.

В рамках демонстрации запущен скрипт обучения моделей (`research/train_model.py`),
который тренирует несколько моделей на датасете диабета из sklearn и логирует
параметры, метрики и артефакты в MLflow.

```bash
make mlflow.up       # Запуск: http://localhost:5001
make mlflow.train    # Обучение моделей
```

![MLflow — главная страница](screenshots/stage1-mlflow-home.png)

![MLflow — эксперименты и runs](screenshots/stage1-mlflow-experiments.png)

## Этап 2. Airflow

Развёрнут Apache Airflow 2.10.5 с LocalExecutor для оркестрации пайплайнов.
Реализованы три DAG-а, покрывающие типовые сценарии ML-проекта:

- **etl_pipeline** — цепочка extract → transform → validate → load
- **ml_training_pipeline** — подготовка данных → обучение → оценка → регистрация модели
- **ml_service_health_check** — почасовая проверка здоровья ML-сервиса

Все DAG-и активированы и запущены множество раз для демонстрации работоспособности.

```bash
make airflow.up      # Запуск: http://localhost:8080
```

![Airflow — DAG-и с историей запусков](screenshots/stage2-airflow-dags.png)

## Этап 3. LakeFS

Развёрнут LakeFS — система версионирования данных, работающая по принципу Git.
Стек включает PostgreSQL 15 для метаданных и MinIO в качестве blockstore.

Продемонстрирован полный рабочий процесс: создание репозитория `ml-data`,
создание ветки `add-training-data`, загрузка CSV-файла с данными
и фиксация изменений через commit.

```bash
make lakefs.up       # Запуск: http://localhost:8001
```

![LakeFS — репозитории](screenshots/stage3-lakefs-repos.png)

![LakeFS — commit с данными](screenshots/stage3-lakefs-commit.png)

## Этап 4. JupyterHub

Развёрнут JupyterHub с JupyterLab в качестве среды разработки.
Базовый образ собран на основе python:3.14-slim с установленными
jupyterhub, jupyterlab и notebook.

```bash
make jupyterhub.up   # Запуск: http://localhost:8888
```

![JupyterHub — JupyterLab](screenshots/stage4-jupyterhub.png)

## Этап 5. ML-сервис

Реализован ML-сервис предсказания прогрессии диабета на основе FastAPI.
Модель обучена на стандартном датасете из sklearn и сериализована в `model.pkl`.

Эндпоинты:
- `GET /health` — проверка здоровья и статуса загрузки модели
- `POST /api/v1/predict` — предсказание по 10 медицинским признакам пациента
- `GET /metrics` — Prometheus-метрики

Реализовано JSON-структурированное логирование, запись предсказаний
в PostgreSQL (вход, выход, время, версия модели) и экспорт метрик
через `starlette-exporter`. В Dockerfile добавлен healthcheck через curl.

```bash
make mlapp.up        # Запуск: http://localhost:8000
make mlapp.test      # Тестирование эндпоинтов
```

![ML-сервис — health endpoint](screenshots/stage5-mlservice-health.png)

![ML-сервис — predict endpoint](screenshots/stage5-mlservice-predict.png)

## Этап 6. Мониторинг

Собран единый стек мониторинга: ML-сервис + Prometheus + Grafana + node-exporter.

Prometheus собирает метрики с трёх целей: собственные метрики, node-exporter
для системных метрик хоста и ML-сервис для метрик приложения.

Grafana-дашборд автоматически провизионируется при запуске и содержит:

**Обзор сервиса** — статус (UP/DOWN), общее число запросов, средняя латентность,
количество 5xx-ошибок, текущий RPS.

**Запросы и латентность** — request rate по эндпоинтам, перцентили латентности
(p50/p95/p99), распределение по кодам ответа, длительность по эндпоинтам.

**Системные метрики** — использование CPU и памяти (графики и gauge),
сетевой трафик по интерфейсам.

```bash
make monitoring.up   # Grafana: http://localhost:3000, Prometheus: http://localhost:9090
```

![Prometheus — targets](screenshots/stage6-prometheus-targets.png)

![Grafana — дашборд ML-сервиса (обзор и запросы)](screenshots/stage6-grafana-dashboard.png)

![Grafana — системные метрики](screenshots/stage6-grafana-system.png)

## Этап 7. Kubernetes-манифесты

Подготовлены манифесты для развёртывания ML-сервиса в Kubernetes:

- **deployment.yaml** — 2 реплики, startup/readiness/liveness probes
- **service.yaml** — ClusterIP на порту 80
- **ingress.yaml** — HTTP-доступ через nginx-ingress
- **configmap.yaml** — конфигурация (MODEL_VERSION, LOG_LEVEL)
- **hpa.yaml** — автоскейлинг 2–8 подов по CPU и памяти

```bash
kubectl apply -f stage7-kubernetes/
```

## Этап 8. Helm Chart

Создан Helm chart для ML-сервиса с полной параметризацией.
Настраиваемые параметры: образ (repository, tag), ресурсы (CPU, memory),
количество реплик, probes, ingress, автоскейлинг (HPA).

Подготовлены примеры конфигураций для production и staging окружений
в директории `examples/`.

```bash
helm install ml-release stage8-helm/ml-service-chart/

# Production-конфигурация
helm install ml-prod stage8-helm/ml-service-chart/ \
  -f stage8-helm/ml-service-chart/examples/values-production.yaml
```

## Этап 9. Prompt Storage

Реализована регистрация версий промптов в MLflow Prompt Storage.
Зарегистрированы 3 промпта, каждый в двух версиях:

- **patient_analysis** — анализ медицинских данных пациента (v1 — базовая, v2 — расширенная)
- **prediction_explanation** — интерпретация предсказания модели (v1 — простая, v2 — структурированная)
- **model_report** — генерация отчёта о производительности модели (v1 — краткий, v2 — для заинтересованных лиц)

```bash
make mlflow.up
make prompts.register
```

![MLflow — список промптов](screenshots/stage9-prompts-list.png)

![MLflow — детали промпта](screenshots/stage9-prompt-detail.png)

## Дополнительные улучшения

Помимо основных требований задания, реализовано:

- **Makefile** — управление всеми сервисами, `make all.up` поднимает всё разом
- **Smoke-тест** (`scripts/smoke_test.sh`) — проверка эндпоинтов мониторинг-стека
- **Docker healthcheck** — для ML-сервиса
- **Grafana auto-provisioning** — дашборд подгружается при старте
- **Helm NOTES.txt** — инструкции после деплоя

## Порты сервисов

Все порты разведены — сервисы можно запускать одновременно без конфликтов.

| Сервис | Порт | Этап |
|--------|------|------|
| MLflow | 5001 | 1 |
| MinIO Console (MLflow) | 9001 | 1 |
| Airflow | 8080 | 2 |
| LakeFS | 8001 | 3 |
| MinIO Console (LakeFS) | 9003 | 3 |
| JupyterHub | 8888 | 4 |
| ML-сервис | 8000 | 5, 6 |
| Prometheus | 9090 | 6 |
| Grafana | 3000 | 6 |

> Порты можно переопределить через переменные в `.env` файлах каждого этапа.
