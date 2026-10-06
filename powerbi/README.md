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

## Как получить данные для Power BI

1. Скачать IBM Telco Customer Churn CSV.
2. Положить файл в:
   `data/WA_Fn-UseC_-Telco-Customer-Churn.csv`
3. Установить зависимости из корня проекта.
4. Запустить:

```bash
python powerbi/prepare_powerbi.py
```

Скрипт создаст:

```text
powerbi/
└── data/
    └── churn_scored.csv
```

В CSV будут исходные customer-level признаки и ML-поля:

- `churn_probability`;
- `risk_bucket`;
- `risk_rank`;
- `risk_percentile`;
- `is_top_5_pct`;
- `is_top_10_pct`;
- `is_top_20_pct`;
- `is_top_30_pct`;
- `is_top_50_pct`.

## Подключение в Power BI

В Power BI Desktop:

**Home → Get data → Text/CSV → `powerbi/data/churn_scored.csv`**

После загрузки таблицы можно строить визуализации непосредственно из customer-level данных.

### Рекомендуемые фильтры

Сверху страницы:

- Contract;
- Internet Service;
- Payment Method;
- tenure segment;
- risk bucket.

Фильтры должны менять все связанные графики, чтобы dashboard можно было использовать как исследовательский инструмент, а не только как статичный отчёт.

## Важный момент по ML

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
