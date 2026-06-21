"""Prototype training script for vitals-based risk estimator."""

import argparse
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

from train_utils import compute_metrics, ensure_dir


FEATURES = ["age", "sbp", "dbp", "heart_rate", "temperature", "respiratory_rate", "spo2", "weight", "glucose"]


def generate_mock_vitals(n: int = 500):
    rng = np.random.default_rng(42)
    X = np.column_stack([
        rng.integers(18, 90, n),
        rng.integers(85, 180, n),
        rng.integers(50, 110, n),
        rng.integers(50, 140, n),
        rng.uniform(96.0, 104.5, n),
        rng.integers(12, 34, n),
        rng.integers(82, 100, n),
        rng.uniform(40.0, 120.0, n),
        rng.integers(70, 220, n),
    ])

    y = np.where((X[:, 6] < 90) | (X[:, 1] < 90) | ((X[:, 4] > 102) & (X[:, 3] > 110)), 2,
                 np.where((X[:, 6] < 94) | (X[:, 5] > 22) | (X[:, 4] > 100.4), 1, 0))
    return X, y


def main(out_path: str):
    X, y = generate_mock_vitals()
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=160, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    metrics = compute_metrics(y_val, y_pred)
    print("Vitals model metrics:", metrics)
    print("Confusion matrix:")
    print(confusion_matrix(y_val, y_pred))

    ensure_dir(os.path.dirname(out_path))
    joblib.dump({"model": model, "features": FEATURES}, out_path)
    print(f"Saved vitals model -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="../models/saved/vitals_model.joblib")
    args = parser.parse_args()
    main(args.out)
