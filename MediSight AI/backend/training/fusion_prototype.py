"""Prototype rule+weight fusion trainer for multimodal ranking calibration."""

import argparse
import json
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from train_utils import compute_metrics, ensure_dir


# Toy feature schema: [image_score, vitals_risk, symptom_density, urgency_hint]

def generate_mock_fusion_data(n=600):
    rng = np.random.default_rng(7)
    X = rng.uniform(0, 1, size=(n, 4))
    y = ((0.45 * X[:, 0] + 0.3 * X[:, 1] + 0.15 * X[:, 2] + 0.1 * X[:, 3]) > 0.55).astype(int)
    return X, y


def main(out_path: str):
    X, y = generate_mock_fusion_data()
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    model = LogisticRegression(max_iter=300)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)

    metrics = compute_metrics(y_val, y_pred)
    print("Fusion prototype metrics:", metrics)

    ensure_dir(os.path.dirname(out_path))
    payload = {
        "coef": model.coef_.tolist(),
        "intercept": model.intercept_.tolist(),
        "feature_schema": ["image_score", "vitals_risk", "symptom_density", "urgency_hint"],
        "metrics": metrics,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved fusion prototype -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="../models/saved/fusion_prototype.json")
    args = parser.parse_args()
    main(args.out)
