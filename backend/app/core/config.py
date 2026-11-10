import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'invoiceflow.db').as_posix()}",
)