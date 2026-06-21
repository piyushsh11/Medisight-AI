import os
from dataclasses import dataclass

import numpy as np
from PIL import Image

from services.disease_catalog import modality_from_image_type
from services.ml_inference import load_keras_model, predict_with_model


@dataclass
class ImageInferenceResult:
    quality_message: str
    findings: list[dict]
    quality_flag: str
    model_status: str
    detected_modality: str


class ImageModelService:
    """Service layer where real trained models can be loaded in future."""

    CHEST_CLASSES = [
        "pneumonia",
        "pleural effusion",
        "pulmonary edema",
        "pneumothorax",
        "no acute finding",
    ]

    SKIN_CLASSES = [
        "eczema",
        "fungal infection",
        "cellulitis suspicion",
        "psoriasis-like lesion",
        "acneiform lesion",
        "suspicious lesion requiring dermatologist review",
    ]

    def __init__(self):
        self._chest_model = None
        self._skin_model = None
        self._models_checked = False

    def _load_models_once(self):
        if self._models_checked:
            return
        self._chest_model = load_keras_model("chest_xray_model.keras")
        self._skin_model = load_keras_model("skin_model.keras")
        self._models_checked = True

    def preprocess(self, image_path: str, size: tuple[int, int] = (224, 224)) -> np.ndarray:
        image = Image.open(image_path).convert("RGB").resize(size)
        arr = np.asarray(image, dtype=np.float32) / 255.0
        return arr

    def quality_check(self, image_path: str) -> tuple[str, str]:
        image = Image.open(image_path)
        width, height = image.size
        if width < 256 or height < 256:
            return "Poor image quality detected (low resolution).", "poor"
        return "Image quality appears acceptable for preliminary analysis.", "acceptable"

    def infer(self, image_path: str, image_type: str) -> ImageInferenceResult:
        image_array = self.preprocess(image_path)
        quality_message, quality_flag = self.quality_check(image_path)
        self._load_models_once()

        image_type = (image_type or "other").lower()
        detected_modality = modality_from_image_type(image_type)
        if detected_modality == "chest_xray":
            if self._chest_model is not None:
                findings = predict_with_model(self._chest_model, image_array, self.CHEST_CLASSES)
                model_status = "trained chest X-ray model"
            else:
                findings = [
                    {"condition": "pneumonia", "likelihood": "moderate", "score": 0.55},
                    {"condition": "pleural effusion", "likelihood": "low", "score": 0.3},
                ]
                model_status = "fallback chest X-ray baseline"
        elif detected_modality == "skin":
            if self._skin_model is not None:
                findings = predict_with_model(self._skin_model, image_array, self.SKIN_CLASSES)
                model_status = "trained skin model"
            else:
                findings = [
                    {"condition": "eczema", "likelihood": "moderate", "score": 0.55},
                    {"condition": "fungal infection", "likelihood": "low", "score": 0.3},
                ]
                model_status = "fallback skin baseline"
        else:
            findings = [
                {"condition": "non-specific imaging pattern", "likelihood": "low", "score": 0.2},
            ]
            model_status = "fallback non-specific baseline"

        return ImageInferenceResult(
            quality_message=quality_message,
            findings=findings,
            quality_flag=quality_flag,
            model_status=model_status,
            detected_modality=detected_modality,
        )


MODEL_SERVICE = ImageModelService()
