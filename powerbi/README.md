# Power BI — Churn & Retention

## Зачем здесь Power BI

Ноутбук отвечает на вопрос **как устроена модель и насколько хорошо она ранжирует клиентов по риску**. Power BI нужен для другой части задачи — быстро показать бизнесу, **где находится churn и кого имеет смысл смотреть в первую очередь**.

Дашборд строится поверх customer-level таблицы, которую можно получить скриптом `prepare_powerbi.py`.

## Структура дашборда

### 1. Churn Overview

Верхний блок:

- Customers — количество клиентов;
- Churn Rate — доля ушедших;
- Avg Monthly Charges — средний ежемесячный платёж;
- Avg Tenure — средний срок обслуживания.

Основные графики:

- churn rate;
- churn по типу контракта;
- churn по сроку обслуживания.

### 2. Customer Segments

Здесь уже не просто общий churn, а сравнение сегментов:

- Contract;
- Internet Service;
- Payment Method;
- tenure segment;
- Monthly Charges.

Главный вопрос:

> **В каких сегментах churn заметно выше и насколько большой этот сегмент?**

Для категориальных признаков лучше использовать одновременно churn rate и количество клиентов. Высокий процент на маленькой группе сам по себе не означает большой бизнес-приоритет.

### 3. ML Risk

Отдельная страница для результата модели:

- Low / Medium / High Risk;
- количество клиентов в каждом сегменте;
- churn rate по risk bucket;
- распределение predicted churn probability;
- top-risk coverage.

Здесь модель уже превращается из технического результата в инструмент приоритизации.

### 4. Retention Prioritization

Главный бизнес-блок проекта.

Показываем:

| Capacity | Что смотрим |
|---|---|
| Top 5% | сколько churn находится в самой рискованной группе |
| Top 10% | coverage при ограниченной команде |
| Top 20% | компромисс между охватом и объёмом работы |
| Top 30% | более широкий retention-сегмент |
| Top 50% | контрольный ориентир |

Основной KPI страницы:

**Share of churn captured**

То есть какая доля клиентов, которые действительно ушли, попадает в выбранную группу риска.

## Данные и визуальная часть

Исходный датасет уже находится в репозитории в `data/WA_Fn-UseC_-Telco-Customer-Churn.csv`.

Для визуальной части подготовлен `dashboard_summary.csv` с ключевыми показателями сегментов. Dashboard preview находится непосредственно в репозитории — ниже видны основные страницы, которые должны быть собраны в Power BI Desktop.

## Dashboard preview

### Overview

![Business overview](screenshots/01_overview.svg)

### Customer risk

![Customer risk](screenshots/02_ml_risk.svg)

### Retention opportunity

![Retention opportunity](screenshots/03_retention.svg)

## Подключение в Power BI

В Power BI используется customer-level таблица с признаками клиента и результатами ML scoring. Dashboard повторяет логику проекта: сначала смотрим структуру churn, затем сегменты, затем risk ranking и capacity-based prioritization.



`risk_bucket` — это не готовая рекомендация «дать скидку».

Модель отвечает на вопрос:

> **кого стоит рассмотреть в первую очередь с точки зрения риска ухода?**

А уже решение о retention-механике требует отдельного эксперимента с treatment/control.

## Результат

В итоге проект разделяет две задачи:

**Python / ML**

данные → preprocessing → модели → probability → risk ranking

**Power BI**

risk ranking → сегменты → capacity → retention prioritization

Такой разделение лучше отражает реальный аналитический workflow: модель не заканчивается на метрике качества, а результат доводится до понятного бизнес-инструмента.
