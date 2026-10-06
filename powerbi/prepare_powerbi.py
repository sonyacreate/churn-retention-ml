"""Подготовка customer-level датасета для Power BI.

Скрипт использует тот же preprocessing и модели, что и основной ML pipeline.
Исходный CSV не сохраняется в репозитории.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

# Позволяет запускать скрипт напрямую из корня репозитория.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.churn_model import (  # noqa: E402
    build_model,
    load_data,
    prepare_features,
)


RAW_PATH = ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
OUTPUT_PATH = ROOT / "powerbi" / "data" / "churn_scored.csv"


def build_models(preprocessor):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    return {
        "logistic_regression": build_model(
            preprocessor,
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            ),
        ),
        "random_forest": build_model(
            preprocessor,
            RandomForestClassifier(
                n_estimators=500,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ),
    }


def main():
    from sklearn.metrics import average_precision_score
    from sklearn.model_selection import train_test_split

    df = load_data(RAW_PATH)
    X, y, preprocessor = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    models = build_models(preprocessor)

    scores = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        probabilities = model.predict_proba(X_test)[:, 1]
        scores[name] = average_precision_score(y_test, probabilities)

    best_name = max(scores, key=scores.get)
    best_model = models[best_name]

    # Для Power BI нужен score всей customer-level базы.
    # Модель при этом обучалась только на train.
    all_probabilities = best_model.predict_proba(X)[:, 1]

    scored = df.copy()
    scored["churn_probability"] = all_probabilities

    scored = scored.sort_values(
        "churn_probability",
        ascending=False
    ).reset_index(drop=True)

    scored["risk_rank"] = np.arange(1, len(scored) + 1)
    scored["risk_percentile"] = scored["risk_rank"] / len(scored)

    scored["risk_bucket"] = pd.cut(
        scored["risk_percentile"],
        bins=[0, 0.20, 0.50, 1.00],
        labels=["High", "Medium", "Low"],
        include_lowest=True,
    ).astype(str)

    for pct in [5, 10, 20, 30, 50]:
        scored[f"is_top_{pct}_pct"] = (
            scored["risk_rank"] <= np.ceil(len(scored) * pct / 100)
        ).astype(int)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(OUTPUT_PATH, index=False)

    print(f"Selected model: {best_name}")
    print(f"Validation PR-AUC: {scores[best_name]:.4f}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
