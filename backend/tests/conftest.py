import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40
_db_path = Path(tempfile.gettempdir()) / "invoiceflow_test.db"
_db_path.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path.as_posix()}"


@pytest.fixture(scope="session", autouse=True)
def seed():
    from app.core.security import hash_password
    from app.db import Company, InvoiceRecord, SessionLocal, User
    from app.main import app
    from tests.helpers import PASSWORD

    password_hash = hash_password(PASSWORD)
    with TestClient(app):
        with SessionLocal() as db:
            a = Company(name="Company A")
            b = Company(name="Company B")
            db.add_all([a, b])
            db.commit()
            for email, role, company in [
                ("admin@a.test", "admin", a),
                ("viewer@a.test", "viewer", a),
                ("lock@a.test", "viewer", a),
                ("admin@b.test", "admin", b),
            ]:
                db.add(
                    User(
                        email=email,
                        password_hash=password_hash,
                        role=role,
                        company_id=company.id,
                    )
                )
            db.add(
                InvoiceRecord(
                    original_name="secret.png",
                    stored_name="secret.png",
                    status="ok",
                    company_id=a.id,
                )
            )
            db.commit()
        yield