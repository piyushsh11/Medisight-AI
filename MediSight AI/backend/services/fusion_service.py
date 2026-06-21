from dataclasses import dataclass

from config import DEFAULT_DISCLAIMER
from services.disease_catalog import FUSION_WEIGHTS, DiseaseProfile, modality_from_image_type, profiles_for_modality


@dataclass
class FusionOutput:
    possible_conditions: list[dict]
    likelihood_band: str
    evidence: list[str]
    abnormal_vitals: list[str]
    extracted_symptoms: list[str]
    urgency: str
    explanation: str
    disclaimer: str
    model_status: str
    detected_modality: str


def _likelihood_to_score(likelihood: str) -> float:
    return {
        "high": 0.85,
        "moderate": 0.55,
        "low": 0.3,
    }.get(str(likelihood or "").lower(), 0.2)


def _image_score(profile: DiseaseProfile, image_findings: list[dict]) -> float:
    best = 0.0
    for finding in image_findings:
        condition = str(finding.get("condition", "")).lower()
        if any(term in condition for term in profile.image_terms):
            best = max(best, float(finding.get("score") or _likelihood_to_score(finding.get("likelihood"))))
    return round(min(best, 1.0), 3)


def _symptom_score(profile: DiseaseProfile, symptoms: list[str]) -> float:
    if not profile.symptom_terms:
        return 0.0
    symptom_set = {str(symptom).lower() for symptom in symptoms}
    matched = sum(1 for term in profile.symptom_terms if term in symptom_set)
    return round(matched / len(profile.symptom_terms), 3)


def _vitals_score(profile: DiseaseProfile, abnormal_vitals: list[str]) -> float:
    if not profile.vital_terms:
        return 0.0
    text = " ".join(abnormal_vitals).lower()
    aliases = {
        "spo2": ("spo2", "oxygen"),
        "temperature": ("temperature", "fever"),
        "heart_rate": ("heart rate", "tachycardia"),
        "respiratory_rate": ("respiratory rate",),
        "sbp": ("sbp", "blood pressure"),
    }
    matched = 0
    for term in profile.vital_terms:
        candidates = aliases.get(term, (term.replace("_", " "),))
        if any(candidate in text for candidate in candidates):
            matched += 1
    return round(matched / len(profile.vital_terms), 3)


def _weighted_score(image_score: float, symptom_score: float, vitals_score: float) -> float:
    return round(
        (FUSION_WEIGHTS["image"] * image_score)
        + (FUSION_WEIGHTS["symptoms"] * symptom_score)
        + (FUSION_WEIGHTS["vitals"] * vitals_score),
        3,
    )


def _band(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "moderate"
    return "low"


def fuse_case(
    image_findings: list[dict],
    abnormal_vitals: list[str],
    symptoms_structured: dict,
    vitals_urgency: str,
    model_status: str = "fallback baseline",
    image_type: str = "",
) -> FusionOutput:
    extracted = symptoms_structured.get("extracted", [])
    detected_modality = modality_from_image_type(image_type)
    candidate_profiles = profiles_for_modality(detected_modality)

    ranked = []
    for profile in candidate_profiles:
        image_component = _image_score(profile, image_findings)
        symptom_component = _symptom_score(profile, extracted)
        vitals_component = _vitals_score(profile, abnormal_vitals)
        final_score = _weighted_score(image_component, symptom_component, vitals_component)
        ranked.append(
            {
                "condition": profile.name,
                "score": final_score,
                "likelihood": _band(final_score),
                "components": {
                    "image": image_component,
                    "symptoms": symptom_component,
                    "vitals": vitals_component,
                },
            }
        )

    ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)[:5]
    top_score = ranked[0]["score"] if ranked else 0.0
    likelihood_band = _band(top_score)

    evidence = [
        f"Detected modality: {detected_modality.replace('_', ' ')}.",
        f"Model status: {model_status}.",
        f"Fusion weights: image {FUSION_WEIGHTS['image']}, symptoms {FUSION_WEIGHTS['symptoms']}, vitals {FUSION_WEIGHTS['vitals']}.",
        f"Imaging cues: {', '.join([f['condition'] for f in image_findings]) or 'none'}",
        f"Vitals abnormalities: {', '.join(abnormal_vitals) if abnormal_vitals else 'none significant'}",
        f"Extracted symptoms: {', '.join(extracted) if extracted else 'limited details'}",
    ]

    if "insufficient symptom detail" in extracted and not abnormal_vitals:
        evidence.append("Limited multimodal evidence; uncertainty is high.")
        likelihood_band = "low"

    urgency = vitals_urgency
    if "breathlessness" in extracted and vitals_urgency not in ("urgent", "moderate"):
        urgency = "moderate"
    if top_score >= 0.75 and urgency == "low":
        urgency = "moderate"

    explanation = (
        "The ranking combines image, symptom, and vitals evidence with fixed research-prototype weights. "
        "If trained image models are available in backend/models/saved, their probabilities feed the image score; "
        "otherwise the system uses transparent fallback baselines. This is clinical decision support only."
    )

    return FusionOutput(
        possible_conditions=ranked,
        likelihood_band=likelihood_band,
        evidence=evidence,
        abnormal_vitals=abnormal_vitals,
        extracted_symptoms=extracted,
        urgency=urgency,
        explanation=explanation,
        disclaimer=DEFAULT_DISCLAIMER,
        model_status=model_status,
        detected_modality=detected_modality,
    )
