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
    permutation_importance,
    brier_score_loss,
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


def permutation_feature_importance(model, X_test, y_test, n_repeats: int = 10) -> pd.DataFrame:
    """Estimate feature importance on the untouched test set.

    Permutation importance is measured on the full pipeline, so importance is
    reported for original customer-level features rather than one-hot columns.
    """
    result = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="average_precision",
        n_repeats=n_repeats,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return (
        pd.DataFrame({
            "feature": X_test.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        })
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )


def threshold_table(y_true, probabilities):
    rows = []
    for threshold in np.arange(0.20, 0.81, 0.05):
        predicted = (probabilities >= threshold).astype(int)
        flagged = int(predicted.sum())
        precision = precision_score(y_true, predicted, zero_division=0)
        recall = recall_score(y_true, predicted, zero_division=0)
        f1 = f1_score(y_true, predicted, zero_division=0)
        churners_captured = int(((predicted == 1) & (y_true == 1)).sum())
        total_churners = int((y_true == 1).sum())
        rows.append(
            {
                "threshold": round(float(threshold), 2),
                "customers_flagged": flagged,
                "share_flagged": flagged / len(y_true),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "churners_captured": churners_captured,
                "share_of_churners_captured": churners_captured / total_churners,
            }
        )
    return pd.DataFrame(rows)


def capacity_threshold_table(y_true, probabilities, capacities=(0.05, 0.10, 0.20, 0.30)):
    """Select the score threshold implied by a fixed retention-team capacity."""
    order = np.argsort(-probabilities)
    y_sorted = np.asarray(y_true)[order]
    p_sorted = np.asarray(probabilities)[order]
    total_churners = int(y_sorted.sum())
    rows = []

    for capacity in capacities:
        n = max(1, int(np.ceil(len(y_true) * capacity)))
        selected_y = y_sorted[:n]
        selected_p = p_sorted[:n]
        captured = int(selected_y.sum())
        rows.append(
            {
                "capacity_share": capacity,
                "customers_contacted": n,
                "implied_threshold": float(selected_p[-1]),
                "precision": float(selected_y.mean()),
                "churners_captured": captured,
                "share_of_churners_captured": captured / total_churners if total_churners else 0.0,
            }
        )
    return pd.DataFrame(rows)


def top_risk_table(y_true, probabilities, shares=(0.05, 0.10, 0.20, 0.30, 0.50)):
    """Evaluate how much observed churn sits inside the highest-risk customers."""
    order = np.argsort(-probabilities)
    y_sorted = np.asarray(y_true)[order]
    total_churners = int(y_sorted.sum())
    rows = []

    for share in shares:
        n = max(1, int(np.ceil(len(y_true) * share)))
        captured = int(y_sorted[:n].sum())
        rows.append(
            {
                "top_share": share,
                "customers": n,
                "churners_captured": captured,
                "share_of_churners_captured": captured / total_churners if total_churners else 0.0,
                "precision": float(y_sorted[:n].mean()),
            }
        )
    return pd.DataFrame(rows)



