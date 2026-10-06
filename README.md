# Customer Churn & Retention — ML

## Business problem

Customer churn is not only a classification problem. The useful question is:

> **Which customers are most likely to leave, and how can a retention team prioritize them?**

This project builds a churn prediction workflow from raw customer-level data and turns model scores into an actionable risk ranking.

The goal is not to maximize accuracy. The focus is on:
- preventing target leakage;
- building reproducible customer features;
- comparing an interpretable baseline with a stronger model;
- evaluating ROC-AUC **and** PR-AUC;
- choosing an operating threshold instead of blindly using 0.5;
- estimating how much of the churn population is captured among the highest-risk customers;
- translating model output into retention segments.

## Dataset

The project uses the public **IBM Telco Customer Churn** dataset.

The dataset is intentionally not committed to the repository. Download the CSV and place it at:

`data/WA_Fn-UseC_-Telco-Customer-Churn.csv`

See [data/README.md](data/README.md) for the expected schema and loading instructions.

## Analytical workflow

1. Data quality and target definition
2. Exploratory analysis of churn
3. Train/test split with stratification
4. Preprocessing inside sklearn pipelines
5. Logistic Regression baseline
6. Tree-based model
7. ROC-AUC / PR-AUC / precision / recall / F1
8. Threshold sensitivity
9. Risk ranking and top-risk customer coverage
10. Feature interpretation
11. Retention recommendations and limitations

## Why PR-AUC matters

Churn is usually the minority class. A model can have a good accuracy while being practically useless for identifying customers who are going to leave.

Therefore the project treats **PR-AUC, recall and precision for the churn class** as important decision metrics alongside ROC-AUC.

## Leakage control

The target is `Churn`. `customerID` is excluded because it is an identifier rather than a predictive customer attribute.

All preprocessing steps are fitted only on the training data through sklearn pipelines. This prevents information from the test set leaking into encoding or scaling.

## Business layer

The model produces a probability of churn for every customer in the test set. Instead of saying "probability > 0.5 = churn", the project also evaluates different thresholds and a top-risk segment.

This separates two questions:

- **prediction:** how well does the model rank churn risk?
- **action:** which customers should a retention team contact first?

A threshold is therefore a business operating point, not a universal mathematical constant.

## Repository structure

```text
churn-retention-ml/
├── data/
│   └── README.md
├── notebooks/
│   └── churn_analysis.ipynb
├── sql/
│   └── customer_features.sql
├── src/
│   └── churn_model.py
├── reports/
│   └── methodology.md
├── requirements.txt
└── README.md
```

## Stack

Python · pandas · NumPy · scikit-learn · SciPy · Matplotlib · seaborn · SQL · Jupyter

## Status

Current version: data validation, leakage-safe feature preparation, Logistic Regression vs Random Forest, ROC-AUC/PR-AUC evaluation, threshold analysis, top-risk targeting and test-set permutation feature interpretation.

Model quality is evaluated on a held-out test set. Final business recommendations are intentionally tied to the observed precision/recall and campaign capacity rather than an arbitrary 0.5 cutoff.
