# Data

The project uses the public IBM Telco Customer Churn dataset.

## Expected file

Place the downloaded CSV here:

```text
data/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

The repository does not store the raw dataset.

## Target

`Churn` is the binary target:
- `Yes` — customer churned
- `No` — customer stayed

## Important columns

The dataset contains customer demographics, account characteristics, subscribed services, contract information, payment method and billing variables.

`customerID` is treated as an identifier and is not used as a model feature.

`TotalCharges` may contain blank strings for customers with very short tenure. These values must be converted to numeric and handled as missing values during preprocessing.

## Reproducibility

Run the project from the repository root after placing the CSV in the path above.
