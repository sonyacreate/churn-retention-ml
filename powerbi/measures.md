# DAX measures для Power BI

Ниже — базовые меры для customer-level таблицы `churn_scored`.

## Основные KPI

```DAX
Customers =
DISTINCTCOUNT(churn_scored[customerID])
```

```DAX
Churned Customers =
CALCULATE(
    [Customers],
    churn_scored[Churn] = "Yes"
)
```

```DAX
Churn Rate =
DIVIDE(
    [Churned Customers],
    [Customers]
)
```

```DAX
Avg Monthly Charges =
AVERAGE(churn_scored[MonthlyCharges])
```

```DAX
Avg Tenure =
AVERAGE(churn_scored[tenure])
```

## Risk

```DAX
High Risk Customers =
CALCULATE(
    [Customers],
    churn_scored[risk_bucket] = "High"
)
```

```DAX
High Risk Churn Rate =
DIVIDE(
    CALCULATE(
        [Churned Customers],
        churn_scored[risk_bucket] = "High"
    ),
    [High Risk Customers]
)
```

## Top-risk coverage

```DAX
Churn Captured Top 10 =
CALCULATE(
    [Churned Customers],
    churn_scored[is_top_10_pct] = 1
)
```

```DAX
Top 10 Churn Coverage =
DIVIDE(
    [Churn Captured Top 10],
    [Churned Customers]
)
```

Аналогично можно сделать меры для Top 5%, 20%, 30% и 50%.

## Как читать dashboard

Если, например, Top 10% показывает высокую долю churn captured, это означает, что модель хорошо концентрирует исторический churn в небольшой группе клиентов.

Это ещё не означает, что retention-кампания даст такой же результат. Для оценки эффекта действия нужен отдельный эксперимент.
