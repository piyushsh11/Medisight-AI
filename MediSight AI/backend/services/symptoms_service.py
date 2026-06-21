import re
from dataclasses import dataclass
from typing import Optional


KEYWORDS = [
    "fever", "cough", "rash", "pain", "itching", "breathlessness",
    "shortness of breath", "fatigue", "chest pain", "headache", "swelling",
    "lesion", "wheezing", "weight loss",
]
SEVERITIES = ["mild", "moderate", "severe"]
BODY_PARTS = ["chest", "skin", "throat", "abdomen", "leg", "arm", "back", "face"]


@dataclass
class SymptomExtraction:
    extracted: list[str]
    duration: Optional[str]
    severity: Optional[str]


def extract_symptoms(text: str) -> SymptomExtraction:
    lowered = (text or "").lower().strip()
    extracted = [kw for kw in KEYWORDS if kw in lowered]
    if "shortness of breath" in extracted and "breathlessness" not in extracted:
        extracted.append("breathlessness")

    duration_match = re.search(r"(\d+\s*(day|days|week|weeks|month|months))", lowered)
    duration = duration_match.group(1) if duration_match else None

    severity = None
    for level in SEVERITIES:
        if level in lowered:
            severity = level
            break

    for part in BODY_PARTS:
        if part in lowered and part not in extracted:
            extracted.append(part)

    if not extracted and len(lowered.split()) < 3:
        extracted.append("insufficient symptom detail")

    return SymptomExtraction(extracted=extracted, duration=duration, severity=severity)
