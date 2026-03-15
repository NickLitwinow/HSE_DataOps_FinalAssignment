"""Регистрация промптов в MLflow Prompt Storage."""

import mlflow
from mlflow import genai

mlflow.set_tracking_uri("http://localhost:5001")


def main():
    # Анализ данных пациента — v1
    genai.register_prompt(
        name="patient_analysis",
        template=(
            "Проанализируй медицинские данные пациента.\n"
            "Показатели: возраст={{ age }}, ИМТ={{ bmi }}, давление={{ bp }}.\n"
            "Предоставь краткое заключение о рисках."
        ),
    )
    print("patient_analysis v1")

    # v2 — расширенная
    genai.register_prompt(
        name="patient_analysis",
        template=(
            "Ты — медицинский ассистент. Проанализируй данные пациента.\n\n"
            "Параметры:\n"
            "- Возраст: {{ age }}\n"
            "- ИМТ: {{ bmi }}\n"
            "- Артериальное давление: {{ bp }}\n"
            "- Уровень холестерина: {{ s1 }}\n"
            "- Уровень сахара: {{ s5 }}\n\n"
            "Предоставь заключение о рисках развития диабета "
            "и рекомендации по профилактике."
        ),
    )
    print("patient_analysis v2")

    # Интерпретация предсказания — v1
    genai.register_prompt(
        name="prediction_explanation",
        template=(
            "Модель предсказала значение прогрессии диабета: {{ prediction }}.\n"
            "Объясни пациенту простым языком, что означает это значение."
        ),
    )
    print("prediction_explanation v1")

    # v2 — с контекстом
    genai.register_prompt(
        name="prediction_explanation",
        template=(
            "Ты — врач-эндокринолог. Пациент получил результат обследования.\n\n"
            "Предсказанное значение прогрессии диабета: {{ prediction }}\n"
            "Норма: до 100. Повышенный риск: 100-200. Высокий риск: выше 200.\n\n"
            "Объясни результат пациенту:\n"
            "1. Что означает это значение\n"
            "2. Какие действия предпринять\n"
            "3. Когда следует обратиться к врачу"
        ),
    )
    print("prediction_explanation v2")

    # Отчёт по модели — v1
    genai.register_prompt(
        name="model_report",
        template=(
            "Сгенерируй отчёт о производительности ML-модели.\n"
            "Название модели: {{ model_name }}\n"
            "Версия: {{ model_version }}\n"
            "RMSE: {{ rmse }}, MAE: {{ mae }}, R2: {{ r2 }}\n"
            "Опиши качество модели и дай рекомендации по улучшению."
        ),
    )
    print("model_report v1")

    # v2 — структурированный
    genai.register_prompt(
        name="model_report",
        template=(
            "Ты — ML-инженер. Подготовь отчёт для заинтересованных лиц.\n\n"
            "## Модель\n"
            "- Название: {{ model_name }}\n"
            "- Версия: {{ model_version }}\n"
            "- Дата обучения: {{ train_date }}\n\n"
            "## Метрики\n"
            "- RMSE: {{ rmse }}\n"
            "- MAE: {{ mae }}\n"
            "- R2: {{ r2 }}\n\n"
            "Составь отчёт по разделам:\n"
            "1. Общая оценка качества\n"
            "2. Сравнение с предыдущей версией\n"
            "3. Рекомендации по улучшению\n"
            "4. Готовность к продакшену"
        ),
    )
    print("model_report v2")

    print("\nВсе промпты зарегистрированы!")


if __name__ == "__main__":
    main()
