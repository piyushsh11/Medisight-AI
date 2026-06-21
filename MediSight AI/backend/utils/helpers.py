import os
import uuid
from datetime import datetime

from werkzeug.utils import secure_filename


def create_case_uid() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"MS-{stamp}-{uuid.uuid4().hex[:6].upper()}"


def safe_filename(original_name: str) -> str:
    base = secure_filename(original_name)
    return f"{uuid.uuid4().hex[:10]}_{base}"


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)
