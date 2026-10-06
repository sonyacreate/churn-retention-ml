-- Customer-level feature preparation for the Telco Churn case.
-- DuckDB syntax.
-- Run from the repository root after placing the raw CSV in data/.

WITH raw AS (
    SELECT *
    FROM read_csv_auto(
        'data/WA_Fn-UseC_-Telco-Customer-Churn.csv',
        header = true,
        nullstr = ''
    )
),

clean AS (
    SELECT
        customerID,
        CAST(tenure AS INTEGER) AS tenure_months,
        CAST(MonthlyCharges AS DOUBLE) AS monthly_charges,
        TRY_CAST(TotalCharges AS DOUBLE) AS total_charges,
        Contract,
        InternetService,
        PaymentMethod,
        PaperlessBilling,
        TechSupport,
        OnlineSecurity,
        StreamingTV,
        StreamingMovies,
        SeniorCitizen,
        Partner,
        Dependents,
        Churn
    FROM raw
),

customer_features AS (
    SELECT
        customerID,
        tenure_months,
        monthly_charges,
        total_charges,

        -- Useful business ratios/features.
        CASE
            WHEN tenure_months > 0
            THEN total_charges / tenure_months
            ELSE monthly_charges
        END AS avg_monthly_spend,

        CASE
            WHEN tenure_months <= 6 THEN '0-6 months'
            WHEN tenure_months <= 12 THEN '7-12 months'
            WHEN tenure_months <= 24 THEN '13-24 months'
            ELSE '24+ months'
        END AS tenure_segment,

        Contract,
        InternetService,
        PaymentMethod,
        PaperlessBilling,
        TechSupport,
        OnlineSecurity,
        StreamingTV,
        StreamingMovies,
        SeniorCitizen,
        Partner,
        Dependents,
        Churn
    FROM clean
)

SELECT *
FROM customer_features;
