import os
from typing import Any

from config import ALLOWED_IMAGE_EXTENSIONS, UPLOAD_FOLDER
from models.db import CaseRecord, db
from services.fusion_service import fuse_case
from services.gemini_service import generate_gemini_interpretation
from services.image_service import MODEL_SERVICE
from services.symptoms_service import extract_symptoms
from services.vitals_service import analyze_vitals, normalize_vitals
from utils.helpers import allowed_file, create_case_uid, ensure_directory, safe_filename
from utils.validation import validate_vitals_payload
from typing import Optional


ensure_directory(UPLOAD_FOLDER)


def create_case_if_missing(case_id: Optional[int] = None) -> CaseRecord:
    if case_id:
        record = db.session.get(CaseRecord, case_id)
        if record:
            return record

    record = CaseRecord(case_uid=create_case_uid())
    db.session.add(record)
    db.session.commit()
    return record


def save_uploaded_image(case_id: Optional[int], file_obj, image_type: str) -> dict[str, Any]:
    if file_obj is None:
        return {"error": "No file uploaded"}

    if not allowed_file(file_obj.filename, ALLOWED_IMAGE_EXTENSIONS):
        return {"error": "Unsupported file type"}

    record = create_case_if_missing(case_id)
    filename = safe_filename(file_obj.filename)
    full_path = os.path.join(UPLOAD_FOLDER, filename)
    file_obj.save(full_path)

    image_result = MODEL_SERVICE.infer(full_path, image_type)

    record.image_path = full_path
    record.image_type = image_type
    record.image_quality = image_result.quality_message
    db.session.commit()

    return {
        "case_id": record.id,
        "case_uid": record.case_uid,
        "image_quality": image_result.quality_message,
        "quality_flag": image_result.quality_flag,
        "image_findings": image_result.findings,
        "model_status": image_result.model_status,
        "detected_modality": image_result.detected_modality,
    }


def save_vitals(case_id: Optional[int], vitals_payload: dict[str, Any]) -> dict[str, Any]:
    ok, message = validate_vitals_payload(vitals_payload)
    if not ok:
        return {"error": message}

    record = create_case_if_missing(case_id)
    normalized = normalize_vitals(vitals_payload)
    vitals_result = analyze_vitals(normalized)

    record.vitals_json = normalized
    record.abnormal_vitals = vitals_result.abnormal_vitals
    record.risk_score = vitals_result.risk_score
    record.urgency = vitals_result.urgency
    db.session.commit()

    return {
        "case_id": record.id,
        "risk_score": vitals_result.risk_score,
        "risk_percent": vitals_result.risk_percent,
        "abnormal_vitals": vitals_result.abnormal_vitals,
        "vitals_assessment": vitals_result.assessment,
        "risk_factors": vitals_result.risk_factors,
        "emergency_flags": vitals_result.emergency_flags,
        "urgency": vitals_result.urgency,
    }


def save_symptoms(case_id: Optional[int], symptoms_text: str) -> dict[str, Any]:
    if not symptoms_text or len(symptoms_text.strip()) < 3:
        return {"error": "Symptoms text too short"}

    record = create_case_if_missing(case_id)
    extracted = extract_symptoms(symptoms_text)

    structured = {
        "extracted": extracted.extracted,
        "duration": extracted.duration,
        "severity": extracted.severity,
    }

    record.symptoms_text = symptoms_text
    record.symptoms_structured = structured
    db.session.commit()

    return {"case_id": record.id, "structured": structured}


def analyze_case(case_id: int) -> dict[str, Any]:
    record = db.session.get(CaseRecord, case_id)
    if not record:
        return {"error": "Case not found"}

    image_result = MODEL_SERVICE.infer(record.image_path, record.image_type) if record.image_path else None
    image_findings = image_result.findings if image_result else []
    model_status = image_result.model_status if image_result else "no image model evidence"
    symptoms_structured = record.symptoms_structured or {"extracted": ["insufficient symptom detail"]}
    abnormal_vitals = record.abnormal_vitals or []
    vitals_urgency = record.urgency or "low"
    vitals_result = analyze_vitals(record.vitals_json) if record.vitals_json else None

    fused = fuse_case(image_findings, abnormal_vitals, symptoms_structured, vitals_urgency, model_status, record.image_type or "")
    if vitals_result and vitals_result.emergency_flags:
        fused.urgency = "urgent"

    payload = {
        "case_id": record.id,
        "case_uid": record.case_uid,
        "reasoning_provider": "gemini",
        "scoring_provider": "local_fusion",
        "possible_conditions": fused.possible_conditions,
        "likelihood_band": fused.likelihood_band,
        "evidence": fused.evidence,
        "abnormal_vitals": fused.abnormal_vitals,
        "extracted_symptoms": fused.extracted_symptoms,
        "detected_modality": fused.detected_modality,
        "vitals_assessment": vitals_result.assessment if vitals_result else [],
        "risk_factors": vitals_result.risk_factors if vitals_result else [],
        "emergency_flags": vitals_result.emergency_flags if vitals_result else [],
        "risk_percent": vitals_result.risk_percent if vitals_result else 0,
        "urgency": fused.urgency,
        "explanation": fused.explanation,
        "image_quality": record.image_quality,
        "model_status": fused.model_status,
        "disclaimer": fused.disclaimer,
        "not_confirmed": True,
    }
    payload["gemini"] = generate_gemini_interpretation(payload)
    if payload["gemini"].get("status") == "ok" and payload["gemini"].get("summary"):
        payload["explanation"] = payload["gemini"]["summary"]
        payload["reasoning_status"] = "gemini"
    else:
        payload["reasoning_status"] = "local_fallback"

    record.result_json = payload
    record.urgency = fused.urgency
    db.session.commit()

    return payload


def get_result(case_id: int) -> dict[str, Any]:
    record = db.session.get(CaseRecord, case_id)
    if not record:
        return {"error": "Case not found"}

    if not record.result_json:
        return {"error": "Case has not been analyzed yet"}

    return record.result_json


def get_history() -> list[dict[str, Any]]:
    rows = CaseRecord.query.order_by(CaseRecord.created_at.desc()).limit(100).all()
    return [r.to_history_dict() for r in rows]
