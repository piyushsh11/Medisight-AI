from typing import Any


def validate_vitals_payload(vitals: dict[str, Any]) -> tuple[bool, str]:
    required = [
        "age", "sex", "sbp", "dbp", "heart_rate", "temperature",
        "respiratory_rate", "spo2", "weight"
    ]
    missing = [k for k in required if k not in vitals or vitals[k] in (None, "")]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    numeric_fields = [
        "age", "sbp", "dbp", "heart_rate", "temperature",
        "respiratory_rate", "spo2", "weight"
    ]
    for field in numeric_fields:
        try:
            float(vitals[field])
        except (TypeError, ValueError):
            return False, f"Invalid numeric value for {field}"

    return True, "ok"
