"""Customer churn modeling pipeline.

Проект сфокусирован на customer-level risk ranking:
модель нужна не только для классификации, но и для приоритизации
клиентов для retention-команды.
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
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    permutation_importance,
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


def threshold_table(y_true, probabilities) -> pd.DataFrame:
    rows = []
    total_churners = int(np.sum(y_true))

    for threshold in np.arange(0.20, 0.81, 0.05):
        predicted = (probabilities >= threshold).astype(int)
        flagged = int(predicted.sum())
        captured = int(((predicted == 1) & (y_true == 1)).sum())

        rows.append({
            "threshold": round(float(threshold), 2),
            "customers_flagged": flagged,
            "share_flagged": flagged / len(y_true),
            "precision": precision_score(y_true, predicted, zero_division=0),
            "recall": recall_score(y_true, predicted, zero_division=0),
            "f1": f1_score(y_true, predicted, zero_division=0),
            "churners_captured": captured,
            "share_of_churners_captured": captured / total_churners if total_churners else 0.0,
        })

    return pd.DataFrame(rows)


def capacity_threshold_table(
    y_true,
    probabilities,
    capacities=(0.05, 0.10, 0.20, 0.30),
) -> pd.DataFrame:
    """Translate retention-team capacity into an operating threshold."""
    order = np.argsort(-probabilities)
    y_sorted = np.asarray(y_true)[order]
    p_sorted = np.asarray(probabilities)[order]
    total_churners = int(y_sorted.sum())
    rows = []

    for capacity in capacities:
        n = max(1, int(np.ceil(len(y_true) * capacity)))
        selected_y = y_sorted[:n]
        captured = int(selected_y.sum())

        rows.append({
            "capacity_share": capacity,
            "customers_contacted": n,
            "implied_threshold": float(p_sorted[n - 1]),
            "precision": float(selected_y.mean()),
            "churners_captured": captured,
            "share_of_churners_captured": (
                captured / total_churners if total_churners else 0.0
            ),
        })

    return pd.DataFrame(rows)


def top_risk_table(
    y_true,
    probabilities,
    shares=(0.05, 0.10, 0.20, 0.30, 0.50),
) -> pd.DataFrame:
    """Measure churn coverage inside the highest-risk customer segments."""
    order = np.argsort(-probabilities)
    y_sorted = np.asarray(y_true)[order]
    total_churners = int(y_sorted.sum())
    rows = []

    for share in shares:
        n = max(1, int(np.ceil(len(y_true) * share)))
        selected_y = y_sorted[:n]
        captured = int(selected_y.sum())

        rows.append({
            "top_share": share,
            "customers": n,
            "churners_captured": captured,
            "share_of_churners_captured": (
                captured / total_churners if total_churners else 0.0
            ),
            "precision": float(selected_y.mean()),
        })

    return pd.DataFrame(rows)


def permutation_feature_importance(
    model,
    X_test,
    y_test,
    n_repeats: int = 10,
) -> pd.DataFrame:
    """Importance of original customer-level features using PR-AUC."""
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


def calibration_metrics(y_true, probabilities) -> dict:
    return {
        "brier_score": brier_score_loss(y_true, probabilities),
        "mean_predicted_probability": float(np.mean(probabilities)),
        "observed_churn_rate": float(np.mean(y_true)),
    }


def build_model(preprocessor, model):
    return Pipeline([
        ("preprocess", preprocessor),
        ("model", model),
    ])


def main():
    df = load_data()
    X, y, preprocessor = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    fitted_models = {}
    probabilities = {}

    print(f"Rows: {len(df):,}")
    print(f"Churn rate: {y.mean():.2%}")

    for name, estimator in models.items():
        model = build_model(preprocessor, estimator)
        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)[:, 1]
        metrics = evaluate(y_test, proba)

        fitted_models[name] = model
        probabilities[name] = proba

        print(f"\n{name}")
        print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"PR-AUC:  {metrics['pr_auc']:.4f}")
        print(f"Precision @ 0.50: {metrics['precision']:.4f}")
        print(f"Recall @ 0.50:    {metrics['recall']:.4f}")
        print(f"F1 @ 0.50:        {metrics['f1']:.4f}")

    best_name = max(
        probabilities,
        key=lambda name: average_precision_score(y_test, probabilities[name]),
    )
    best_model = fitted_models[best_name]
    best_proba = probabilities[best_name]

    print(f"\nSelected model for business analysis: {best_name}")

    print("\nThreshold analysis")
    print(threshold_table(y_test.to_numpy(), best_proba).round(4).to_string(index=False))

    print("\nCapacity-based operating points")
    print(
        capacity_threshold_table(y_test.to_numpy(), best_proba)
        .round(4)
        .to_string(index=False)
    )

    print("\nTop-risk coverage")
    print(
        top_risk_table(y_test.to_numpy(), best_proba)
        .round(4)
        .to_string(index=False)
    )

    print("\nCalibration")
    print(pd.Series(calibration_metrics(y_test, best_proba)).round(4).to_string())

    print("\nTop permutation features")
    print(
        permutation_feature_importance(best_model, X_test, y_test)
        .head(15)
        .round(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
