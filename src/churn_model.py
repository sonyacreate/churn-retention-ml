"""Customer churn modeling pipeline.

The module focuses on ranking churn risk for retention prioritization,
not on maximizing raw classification accuracy.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_PATH = Path("data/WA_Fn-UseC_-Telco-Customer-Churn.csv")
RANDOM_STATE = 42


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"customerID", "Churn"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["Churn"] = df["Churn"].map({"No": 0, "Yes": 1})

    if df["Churn"].isna().any():
        raise ValueError("Unexpected values found in Churn.")

    return df


def prepare_features(df: pd.DataFrame):
    data = df.drop(columns=["customerID"]).copy()
    X = data.drop(columns=["Churn"])
    y = data["Churn"].astype(int)

    categorical = X.select_dtypes(include=["object"]).columns.tolist()
    numeric = X.select_dtypes(exclude=["object"]).columns.tolist()

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, numeric),
        ("cat", categorical_pipe, categorical),
    ])

    return X, y, preprocessor


def evaluate(y_true, probabilities, threshold: float = 0.5) -> dict:
    predictions = (probabilities >= threshold).astype(int)

    return {
        "threshold": threshold,
        "roc_auc": roc_auc_score(y_true, probabilities),
        "pr_auc": average_precision_score(y_true, probabilities),
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, predictions).tolist(),
    }


def threshold_table(y_true, probabilities, thresholds=None) -> pd.DataFrame:
    if thresholds is None:
        thresholds = np.arange(0.20, 0.81, 0.05)

    rows = []
    actual_churners = int(np.sum(y_true == 1))

    for threshold in thresholds:
        predictions = (probabilities >= threshold).astype(int)
        contacted = int(predictions.sum())
        captured = int(((predictions == 1) & (y_true == 1)).sum())

        rows.append({
            "threshold": round(float(threshold), 2),
            "customers_flagged": contacted,
            "share_flagged": contacted / len(y_true),
            "precision": precision_score(y_true, predictions, zero_division=0),
            "recall": recall_score(y_true, predictions, zero_division=0),
            "f1": f1_score(y_true, predictions, zero_division=0),
            "churners_captured": captured,
            "share_of_churners_captured": (
                captured / actual_churners if actual_churners else np.nan
            ),
        })

    return pd.DataFrame(rows)


def main() -> None:
    df = load_data()
    X, y, preprocessor = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    logistic = Pipeline([
        ("preprocessor", preprocessor),
        ("model", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    _, _, rf_preprocessor = prepare_features(df)
    random_forest = Pipeline([
        ("preprocessor", rf_preprocessor),
        ("model", RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ])

    models = {
        "logistic_regression": logistic,
        "random_forest": random_forest,
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        probabilities = model.predict_proba(X_test)[:, 1]

        print(f"\\n{name}")
        for key, value in evaluate(y_test, probabilities).items():
            print(f"{key}: {value}")

        print("\\nThreshold analysis:")
        print(threshold_table(y_test, probabilities).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
