#!/bin/bash
# Smoke-тест для проверки ML-сервиса и мониторинга
# Использование: ./scripts/smoke_test.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  $name"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${NC}  $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "ML-сервис"
check "Health endpoint" \
    "curl -sf http://localhost:8000/health | grep -q ok"

check "Predict endpoint" \
    "curl -sf -X POST http://localhost:8000/api/v1/predict \
        -H 'Content-Type: application/json' \
        -d '{\"age\":0.05,\"sex\":0.05,\"bmi\":0.06,\"bp\":0.02,\"s1\":-0.04,\"s2\":-0.03,\"s3\":-0.04,\"s4\":0.03,\"s5\":0.04,\"s6\":-0.01}' \
        | grep -q predict"

check "Metrics endpoint" \
    "curl -sf http://localhost:8000/metrics | grep -q starlette_requests"

echo ""
echo "Мониторинг"
check "Prometheus ready" \
    "curl -sf http://localhost:9090/-/ready | grep -q Ready"

check "Prometheus targets" \
    "curl -sf http://localhost:9090/api/v1/targets | grep -q mlapp"

check "Grafana доступна" \
    "curl -sf -o /dev/null -w '%{http_code}' http://localhost:3000 | grep -qE '200|302'"

echo ""
echo "Результат"
TOTAL=$((PASS + FAIL))
echo -e "Пройдено: ${GREEN}${PASS}${NC}/${TOTAL}"
if [ "$FAIL" -gt 0 ]; then
    echo -e "Провалено: ${RED}${FAIL}${NC}/${TOTAL}"
    exit 1
fi
echo "Все проверки пройдены!"
