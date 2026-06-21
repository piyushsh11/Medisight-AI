"""Disease targets and evidence weights for research-prototype fusion."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiseaseProfile:
    name: str
    modalities: tuple[str, ...]
    symptom_terms: tuple[str, ...]
    vital_terms: tuple[str, ...]
    image_terms: tuple[str, ...]


DISEASE_PROFILES = [
    DiseaseProfile(
        name="pneumonia",
        modalities=("chest_xray",),
        symptom_terms=("fever", "cough", "breathlessness", "chest"),
        vital_terms=("spo2", "temperature", "heart_rate", "respiratory_rate"),
        image_terms=("pneumonia", "opacity", "consolidation"),
    ),
    DiseaseProfile(
        name="pleural effusion",
        modalities=("chest_xray",),
        symptom_terms=("breathlessness", "chest pain", "chest"),
        vital_terms=("spo2", "respiratory_rate"),
        image_terms=("pleural effusion", "effusion"),
    ),
    DiseaseProfile(
        name="pulmonary edema",
        modalities=("chest_xray",),
        symptom_terms=("breathlessness", "fatigue", "chest"),
        vital_terms=("spo2", "respiratory_rate", "heart_rate"),
        image_terms=("pulmonary edema", "edema"),
    ),
    DiseaseProfile(
        name="pneumothorax",
        modalities=("chest_xray",),
        symptom_terms=("chest pain", "breathlessness", "chest"),
        vital_terms=("spo2", "respiratory_rate", "heart_rate"),
        image_terms=("pneumothorax",),
    ),
    DiseaseProfile(
        name="eczema",
        modalities=("skin",),
        symptom_terms=("rash", "itching", "skin"),
        vital_terms=(),
        image_terms=("eczema",),
    ),
    DiseaseProfile(
        name="fungal infection",
        modalities=("skin",),
        symptom_terms=("rash", "itching", "skin"),
        vital_terms=(),
        image_terms=("fungal infection",),
    ),
    DiseaseProfile(
        name="cellulitis suspicion",
        modalities=("skin",),
        symptom_terms=("pain", "swelling", "skin", "fever"),
        vital_terms=("temperature", "heart_rate"),
        image_terms=("cellulitis",),
    ),
    DiseaseProfile(
        name="psoriasis-like lesion",
        modalities=("skin",),
        symptom_terms=("rash", "itching", "skin"),
        vital_terms=(),
        image_terms=("psoriasis",),
    ),
    DiseaseProfile(
        name="acneiform lesion",
        modalities=("skin",),
        symptom_terms=("skin", "face"),
        vital_terms=(),
        image_terms=("acne", "acneiform"),
    ),
    DiseaseProfile(
        name="suspicious lesion requiring dermatologist review",
        modalities=("skin",),
        symptom_terms=("skin", "lesion"),
        vital_terms=(),
        image_terms=("suspicious lesion", "melanoma"),
    ),
]


FUSION_WEIGHTS = {
    "image": 0.5,
    "symptoms": 0.3,
    "vitals": 0.2,
}


def get_profile(condition: str) -> Optional[DiseaseProfile]:
    normalized = condition.strip().lower()
    return next((profile for profile in DISEASE_PROFILES if profile.name == normalized), None)


def modality_from_image_type(image_type: str) -> str:
    normalized = (image_type or "").strip().lower()
    if "skin" in normalized:
        return "skin"
    if "chest" in normalized or "x-ray" in normalized or "xray" in normalized:
        return "chest_xray"
    return "general"


def profiles_for_modality(modality: str) -> list[DiseaseProfile]:
    if modality == "general":
        return DISEASE_PROFILES
    return [profile for profile in DISEASE_PROFILES if modality in profile.modalities]
