"""Inference helpers for loading trained models from backend/models/saved.
Replace placeholder fallback logic with real model inference as datasets become available.
"""

import os

import numpy as np


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVED_DIR = os.path.join(BASE_DIR, "models", "saved")


def load_keras_model(model_name: str):
    model_path = os.path.join(SAVED_DIR, model_name)
    if not os.path.exists(model_path):
        return None

    try:
        import tensorflow as tf
    except Exception:  # pragma: no cover - tensorflow optional in lightweight runs
        return None

    return tf.keras.models.load_model(model_path)


def predict_with_model(model, image_array: np.ndarray, class_names: list[str]) -> list[dict]:
    if model is None:
        # Placeholder ranking if no trained model exists yet.
        return [{"condition": class_names[0], "likelihood": "low", "score": 0.25}]

    preds = model.predict(np.expand_dims(image_array, axis=0), verbose=0)[0]
    top_idx = np.argsort(preds)[::-1][:3]
    output = []
    for idx in top_idx:
        score = float(preds[idx])
        band = "high" if score >= 0.75 else "moderate" if score >= 0.45 else "low"
        output.append({"condition": class_names[int(idx)], "likelihood": band, "score": round(score, 3)})
    return output
