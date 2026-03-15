.PHONY: help
help: ## Показать справку по командам
	@grep -E '^[a-zA-Z0-9._-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'


# Запуск всего проекта
.PHONY: all.up all.down
all.up: ## Запустить все сервисы одновременно (stages 1-4 + 6)
	docker compose -f stage1-mlflow/docker-compose.yaml up -d --build
	docker compose -f stage2-airflow/docker-compose.yaml up -d
	docker compose -f stage3-lakefs/docker-compose.yaml up -d --build
	docker compose -f stage4-jupyterhub/docker-compose.yaml up -d --build
	docker compose -f stage6-monitoring/docker-compose.yaml up -d --build
	@echo ""
	@echo "Все сервисы запущены:"
	@echo "  MLflow:       http://localhost:5001"
	@echo "  MinIO (MLflow): http://localhost:9001"
	@echo "  Airflow:      http://localhost:8080"
	@echo "  LakeFS:       http://localhost:8001"
	@echo "  MinIO (LakeFS): http://localhost:9003"
	@echo "  JupyterHub:   http://localhost:8888"
	@echo "  ML-сервис:    http://localhost:8000"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Grafana:      http://localhost:3000"

all.down: ## Остановить все сервисы
	docker compose -f stage6-monitoring/docker-compose.yaml down 2>/dev/null || true
	docker compose -f stage5-ml-service/docker-compose.yaml down 2>/dev/null || true
	docker compose -f stage4-jupyterhub/docker-compose.yaml down 2>/dev/null || true
	docker compose -f stage3-lakefs/docker-compose.yaml down 2>/dev/null || true
	docker compose -f stage2-airflow/docker-compose.yaml down 2>/dev/null || true
	docker compose -f stage1-mlflow/docker-compose.yaml down 2>/dev/null || true


# Stage 1: MLflow
.PHONY: mlflow.up mlflow.down mlflow.logs
mlflow.up: ## Запустить MLflow + PostgreSQL + MinIO
	docker compose -f stage1-mlflow/docker-compose.yaml up -d --build

mlflow.down: ## Остановить MLflow
	docker compose -f stage1-mlflow/docker-compose.yaml down

mlflow.logs: ## Показать логи MLflow
	docker compose -f stage1-mlflow/docker-compose.yaml logs -f mlflow

mlflow.train: ## Запустить обучение моделей и логирование в MLflow
	cd stage1-mlflow && python research/train_model.py


# Stage 2: Airflow
.PHONY: airflow.up airflow.down airflow.logs
airflow.up: ## Запустить Airflow + PostgreSQL
	docker compose -f stage2-airflow/docker-compose.yaml up -d

airflow.down: ## Остановить Airflow
	docker compose -f stage2-airflow/docker-compose.yaml down

airflow.logs: ## Показать логи Airflow webserver
	docker compose -f stage2-airflow/docker-compose.yaml logs -f airflow-webserver


# Stage 3: LakeFS
.PHONY: lakefs.up lakefs.down lakefs.logs
lakefs.up: ## Запустить LakeFS + PostgreSQL + MinIO
	docker compose -f stage3-lakefs/docker-compose.yaml up -d --build

lakefs.down: ## Остановить LakeFS
	docker compose -f stage3-lakefs/docker-compose.yaml down

lakefs.logs: ## Показать логи LakeFS
	docker compose -f stage3-lakefs/docker-compose.yaml logs -f lakefs


# Stage 4: JupyterHub
.PHONY: jupyterhub.up jupyterhub.down jupyterhub.logs
jupyterhub.up: ## Запустить JupyterHub
	docker compose -f stage4-jupyterhub/docker-compose.yaml up -d --build

jupyterhub.down: ## Остановить JupyterHub
	docker compose -f stage4-jupyterhub/docker-compose.yaml down

jupyterhub.logs: ## Показать логи JupyterHub
	docker compose -f stage4-jupyterhub/docker-compose.yaml logs -f jupyterhub


# Stage 5: ML-сервис (standalone, без мониторинга)
.PHONY: mlapp.up mlapp.down mlapp.logs mlapp.test
mlapp.up: ## Запустить ML-сервис + PostgreSQL (standalone)
	docker compose -f stage5-ml-service/docker-compose.yaml up -d --build

mlapp.down: ## Остановить ML-сервис
	docker compose -f stage5-ml-service/docker-compose.yaml down

mlapp.logs: ## Показать логи ML-сервиса
	docker compose -f stage5-ml-service/docker-compose.yaml logs -f mlapp

mlapp.test: ## Тестировать ML-сервис (health + predict)
	@echo "=== Health ===" && \
	curl -s http://localhost:8000/health | python3 -m json.tool && \
	echo "\n=== Predict ===" && \
	curl -s -X POST http://localhost:8000/api/v1/predict \
		-H "Content-Type: application/json" \
		-d '{"age":0.05,"sex":0.05,"bmi":0.06,"bp":0.02,"s1":-0.04,"s2":-0.03,"s3":-0.04,"s4":0.03,"s5":0.04,"s6":-0.01}' \
		| python3 -m json.tool


# Stage 6: Мониторинг (ML-сервис + Prometheus + Grafana)
.PHONY: monitoring.up monitoring.down monitoring.logs
monitoring.up: ## Запустить полный стек мониторинга
	docker compose -f stage6-monitoring/docker-compose.yaml up -d --build

monitoring.down: ## Остановить мониторинг
	docker compose -f stage6-monitoring/docker-compose.yaml down

monitoring.logs: ## Показать логи мониторинга
	docker compose -f stage6-monitoring/docker-compose.yaml logs -f


# Stage 9: Промпты
.PHONY: prompts.register
prompts.register: ## Зарегистрировать промпты в MLflow Prompt Storage
	python stage9-prompts/register_prompts.py


# Утилиты
.PHONY: status smoke-test
smoke-test: ## Запустить smoke-тест мониторинга (stage6 должен быть запущен)
	./scripts/smoke_test.sh

status: ## Показать статус всех контейнеров проекта
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | \
		grep -E "NAMES|mlflow|airflow|lakefs|jupyterhub|mlapp|mlservice|prometheus|grafana|node-exporter|minio" || \
		echo "Контейнеры не запущены"
