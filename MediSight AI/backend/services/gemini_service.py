"""Gemini-powered clinical summary generation.

The Gemini layer only receives structured evidence from MediSight. It should
explain and summarize; it should not override local triage or claim diagnosis.
"""

import json
import urllib.error
import urllib.request
from typing import Any

from config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL, GEMINI_TIMEOUT_SECONDS


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _fallback_interpretation(status: str, message: str) -> dict[str, Any]:
    return {
        "provider": "gemini",
        "status": status,
        "model": GEMINI_MODEL,
        "is_default_reasoning": True,
        "summary": message,
        "why_suggested": [],
        "recommendations": [
            "Review the ranked conditions with a licensed clinician.",
            "Correlate with physical examination and appropriate lab or imaging follow-up.",
        ],
        "red_flags": [
            "Seek urgent care for breathing difficulty, chest pain, confusion, fainting, very low SpO2, or rapidly worsening symptoms.",
        ],
        "follow_up_questions": [
            "When did symptoms begin?",
            "Are symptoms worsening, improving, or stable?",
            "Any relevant medical history, medications, allergies, or recent exposures?",
        ],
        "limitations": [
            "Gemini is the default reasoning provider, but it was not used for this result because it is unavailable.",
            "This system is clinical decision support only and not a confirmed diagnosis.",
        ],
    }


def _candidate_models() -> list[str]:
    models = [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]
    unique = []
    for model in models:
        if model and model not in unique:
            unique.append(model)
    return unique


def _build_prompt(case_payload: dict[str, Any]) -> str:
    compact_case = {
        "detected_modality": case_payload.get("detected_modality"),
        "possible_conditions": case_payload.get("possible_conditions", [])[:5],
        "likelihood_band": case_payload.get("likelihood_band"),
        "urgency": case_payload.get("urgency"),
        "risk_percent": case_payload.get("risk_percent"),
        "vitals_assessment": case_payload.get("vitals_assessment", []),
        "risk_factors": case_payload.get("risk_factors", []),
        "emergency_flags": case_payload.get("emergency_flags", []),
        "abnormal_vitals": case_payload.get("abnormal_vitals", []),
        "extracted_symptoms": case_payload.get("extracted_symptoms", []),
        "evidence": case_payload.get("evidence", []),
        "model_status": case_payload.get("model_status"),
    }
    return (
        "You are helping generate a doctor-facing clinical decision-support summary for a hackathon prototype. "
        "Do not diagnose. Do not prescribe medication. Do not invent missing patient details. "
        "Use cautious language: possible, suggests, consider, requires clinician review. "
        "If emergency flags or urgent vitals are present, prioritize urgent evaluation. "
        "Use the local probability ranking as evidence, but reason across symptoms, vitals, modality, urgency, and red flags. "
        "Return only valid JSON with keys: summary, why_suggested, recommendations, red_flags, "
        "follow_up_questions, limitations. Each list should contain short strings.\n\n"
        f"Structured MediSight evidence:\n{json.dumps(compact_case, indent=2)}"
    )


def _extract_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _request_gemini(model: str, request_payload: dict[str, Any]) -> dict[str, Any]:
    url = GEMINI_ENDPOINT.format(model=model)
    req = urllib.request.Request(
        url,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def generate_gemini_interpretation(case_payload: dict[str, Any]) -> dict[str, Any]:
    if not GEMINI_API_KEY:
        return _fallback_interpretation(
            "disabled",
            "Gemini is not configured. Set GEMINI_API_KEY to enable AI-generated clinical summaries.",
        )

    request_payload = {
        "contents": [{"role": "user", "parts": [{"text": _build_prompt(case_payload)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 900,
        },
    }
    errors = []
    try:
        for model in _candidate_models():
            try:
                response_payload = _request_gemini(model, request_payload)
                parsed = _parse_json_text(_extract_text(response_payload))
                return {
                    "provider": "gemini",
                    "status": "ok",
                    "model": model,
                    "is_default_reasoning": True,
                    "summary": str(parsed.get("summary", "")).strip(),
                    "why_suggested": list(parsed.get("why_suggested", []))[:6],
                    "recommendations": list(parsed.get("recommendations", []))[:6],
                    "red_flags": list(parsed.get("red_flags", []))[:6],
                    "follow_up_questions": list(parsed.get("follow_up_questions", []))[:6],
                    "limitations": list(parsed.get("limitations", []))[:6],
                }
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError) as exc:
                errors.append(f"{model}: {exc}")
    except Exception as exc:
        errors.append(f"unexpected: {exc}")

    return _fallback_interpretation(
        "error",
        "Gemini could not generate a summary after trying the configured fallback models. "
        f"MediSight is showing local evidence only. Errors: {' | '.join(errors)}",
    )
