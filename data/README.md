# Данные

В репозитории уже находится исходный CSV датасета **IBM Telco Customer Churn**:

`data/WA_Fn-UseC_-Telco-Customer-Churn.csv`

Датасет содержит 7 043 клиента и используется для анализа customer churn, сегментации и ML-моделирования.

Целевая переменная:

- `Churn = Yes` — клиент ушёл;
- `Churn = No` — клиент остался.

`customerID` используется как идентификатор и не передаётся в модель.

`TotalCharges` переводится в numeric; пропуски обрабатываются внутри preprocessing pipeline.

Для визуальной части проекта также подготовлен набор агрегированных показателей:

`powerbi/dashboard_summary.csv`

Исходные данные — публичный учебный датасет IBM Telco Customer Churn.
