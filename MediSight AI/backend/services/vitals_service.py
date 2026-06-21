from dataclasses import dataclass


@dataclass
class VitalsResult:
    abnormal_vitals: list[str]
    risk_score: float
    risk_percent: int
    urgency: str
    risk_factors: list[str]
    emergency_flags: list[str]
    assessment: list[dict]


def normalize_vitals(vitals: dict) -> dict:
    normalized = {
        "age": float(vitals.get("age")),
        "sex": str(vitals.get("sex", "")).strip().lower(),
        "sbp": float(vitals.get("sbp")),
        "dbp": float(vitals.get("dbp")),
        "heart_rate": float(vitals.get("heart_rate")),
        "temperature": float(vitals.get("temperature")),
        "respiratory_rate": float(vitals.get("respiratory_rate")),
        "spo2": float(vitals.get("spo2")),
        "weight": float(vitals.get("weight")),
        "glucose": float(vitals.get("glucose")) if vitals.get("glucose") not in (None, "") else None,
    }
    return normalized


def analyze_vitals(vitals: dict) -> VitalsResult:
    abnormal = []
    assessment = []
    risk_factors = []
    emergency_flags = []
    score = 0.0
    urgency = "routine"

    if vitals["spo2"] < 90:
        abnormal.append(f"SpO2 critically low ({vitals['spo2']}%)")
        assessment.append({"label": "SpO2", "value": f"{vitals['spo2']}%", "status": "critical", "direction": "down"})
        risk_factors.append("Hypoxemia")
        emergency_flags.append("Critical oxygen saturation")
        score += 3.0
        urgency = "urgent"
    elif vitals["spo2"] < 94:
        abnormal.append(f"SpO2 below normal ({vitals['spo2']}%)")
        assessment.append({"label": "SpO2", "value": f"{vitals['spo2']}%", "status": "abnormal", "direction": "down"})
        risk_factors.append("Low oxygen saturation")
        score += 1.5

    if vitals["temperature"] >= 102.0 and vitals["heart_rate"] > 110:
        abnormal.append("High fever with tachycardia")
        risk_factors.append("High fever with tachycardia")
        emergency_flags.append("Fever and tachycardia combination")
        score += 2.0
        urgency = "urgent" if urgency != "urgent" else urgency

    if vitals["sbp"] < 90:
        abnormal.append(f"Dangerously low SBP ({vitals['sbp']} mmHg)")
        assessment.append({"label": "Systolic BP", "value": f"{vitals['sbp']} mmHg", "status": "critical", "direction": "down"})
        risk_factors.append("Hypotension")
        emergency_flags.append("Dangerously low systolic blood pressure")
        score += 2.5
        urgency = "urgent"
    elif vitals["sbp"] >= 140 or vitals["dbp"] >= 90:
        abnormal.append(f"Blood pressure elevated ({vitals['sbp']}/{vitals['dbp']} mmHg)")
        assessment.append({"label": "Blood Pressure", "value": f"{vitals['sbp']}/{vitals['dbp']} mmHg", "status": "abnormal", "direction": "up"})
        risk_factors.append("Elevated blood pressure")
        score += 0.8

    if vitals["respiratory_rate"] > 22:
        abnormal.append(f"Respiratory rate elevated ({vitals['respiratory_rate']}/min)")
        status = "critical" if vitals["respiratory_rate"] >= 30 else "abnormal"
        assessment.append({"label": "Respiratory Rate", "value": f"{vitals['respiratory_rate']}/min", "status": status, "direction": "up"})
        risk_factors.append("Tachypnea")
        if vitals["respiratory_rate"] >= 30:
            emergency_flags.append("Severely elevated respiratory rate")
        score += 1.0

    if vitals["temperature"] > 100.4:
        abnormal.append(f"Temperature elevated ({vitals['temperature']} F)")
        assessment.append({"label": "Temperature", "value": f"{vitals['temperature']} F", "status": "abnormal", "direction": "up"})
        risk_factors.append("Fever")
        score += 0.7

    if vitals["heart_rate"] > 100:
        abnormal.append(f"Heart rate elevated ({vitals['heart_rate']} bpm)")
        assessment.append({"label": "Heart Rate", "value": f"{vitals['heart_rate']} bpm", "status": "abnormal", "direction": "up"})
        risk_factors.append("Tachycardia")
        score += 0.6
    elif vitals["heart_rate"] < 50:
        abnormal.append(f"Heart rate low ({vitals['heart_rate']} bpm)")
        assessment.append({"label": "Heart Rate", "value": f"{vitals['heart_rate']} bpm", "status": "abnormal", "direction": "down"})
        risk_factors.append("Bradycardia")
        score += 0.8

    if vitals.get("glucose") is not None:
        if vitals["glucose"] >= 200:
            abnormal.append(f"Glucose elevated ({vitals['glucose']} mg/dL)")
            assessment.append({"label": "Glucose", "value": f"{vitals['glucose']} mg/dL", "status": "abnormal", "direction": "up"})
            risk_factors.append("Hyperglycemia")
            score += 0.6
        elif vitals["glucose"] < 70:
            abnormal.append(f"Glucose low ({vitals['glucose']} mg/dL)")
            assessment.append({"label": "Glucose", "value": f"{vitals['glucose']} mg/dL", "status": "critical", "direction": "down"})
            risk_factors.append("Hypoglycemia")
            emergency_flags.append("Low blood glucose")
            score += 1.5

    if not abnormal:
        urgency = "low"
        assessment.append({"label": "Vitals", "value": "Within expected screening range", "status": "normal", "direction": "flat"})

    if urgency != "urgent":
        if score >= 2.5:
            urgency = "moderate"
        elif score < 1.0:
            urgency = "low"

    deduped_factors = list(dict.fromkeys(risk_factors))
    deduped_flags = list(dict.fromkeys(emergency_flags))
    risk_percent = min(100, round((score / 6.0) * 100))

    return VitalsResult(
        abnormal_vitals=abnormal,
        risk_score=round(score, 2),
        risk_percent=risk_percent,
        urgency=urgency,
        risk_factors=deduped_factors,
        emergency_flags=deduped_flags,
        assessment=assessment,
    )
