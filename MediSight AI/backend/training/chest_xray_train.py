"""Training script for chest X-ray classifier.
If no dataset path is provided, it uses a synthetic placeholder dataset for pipeline testing.
"""

import argparse
import os

import numpy as np
import tensorflow as tf
from sklearn.preprocessing import LabelBinarizer

from train_utils import compute_metrics, ensure_dir, maybe_build_mock_image_dataset, split_data
from typing import Optional


CLASSES = ["pneumonia", "pleural effusion", "pulmonary edema", "pneumothorax", "no acute finding"]


def build_model(num_classes: int):
    base = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3), include_top=False, weights="imagenet", pooling="avg"
    )
    base.trainable = False
    x = tf.keras.layers.Dropout(0.2)(base.output)
    out = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs=base.input, outputs=out)
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def load_dataset(dataset_dir: Optional[str]):
    # Insert real chest X-ray dataset loading logic here when available.
    if dataset_dir and os.path.exists(dataset_dir):
        # Placeholder: implement directory walk -> image tensor + label extraction.
        pass
    return maybe_build_mock_image_dataset(n=220, num_classes=len(CLASSES))


def main(dataset_dir: Optional[str], out_path: str):
    X, y = load_dataset(dataset_dir)
    X_train, X_val, y_train, y_val = split_data(X, y)

    lb = LabelBinarizer()
    y_train_ohe = lb.fit_transform(y_train)
    y_val_ohe = lb.transform(y_val)

    model = build_model(len(CLASSES))
    model.fit(X_train, y_train_ohe, validation_data=(X_val, y_val_ohe), epochs=2, batch_size=16, verbose=1)

    preds = model.predict(X_val, verbose=0)
    y_pred = np.argmax(preds, axis=1)
    metrics = compute_metrics(y_val, y_pred)
    print("Chest X-ray metrics:", metrics)

    ensure_dir(os.path.dirname(out_path))
    model.save(out_path)
    print(f"Saved chest model -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default=None)
    parser.add_argument("--out", default="../models/saved/chest_xray_model.keras")
    args = parser.parse_args()
    main(args.dataset_dir, args.out)