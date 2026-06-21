"""Optional script to seed sample cases into SQLite for demo history."""

import json
import os

from app import create_app
from models.db import CaseRecord, db


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PATH = os.path.join(BASE_DIR, "database", "sample_cases.json")


def main():
    app = create_app()
    with app.app_context():
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            rows = json.load(f)

        for row in rows:
            exists = CaseRecord.query.filter_by(case_uid=row["case_uid"]).first()
            if exists:
                continue
            record = CaseRecord(
                case_uid=row["case_uid"],
                image_type=row.get("image_type"),
                symptoms_text=row.get("symptoms_text"),
                urgency=row.get("urgency"),
            )
            db.session.add(record)

        db.session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    main()
