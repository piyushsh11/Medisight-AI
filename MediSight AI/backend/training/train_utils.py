import os
from typing import Tuple

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


def split_data(X, y, test_size: float = 0.2, random_state: int = 42):
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def compute_metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def maybe_build_mock_image_dataset(n: int, num_classes: int, shape: Tuple[int, int, int] = (224, 224, 3)):
    X = np.random.rand(n, *shape).astype("float32")
    y = np.random.randint(0, num_classes, size=(n,))
    return X, y


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
