from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import login


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_fake_pdf_is_rejected():
    client, _ = login("admin@a.test")
    r = client.post("/invoices", files={"file": ("fake.pdf", b"this is not a pdf", "application/pdf")})
    assert r.status_code == 415


def test_oversized_file_is_rejected():
    client, _ = login("admin@a.test")
    big = b"%PDF" + b"0" * (10 * 1024 * 1024 + 10)
    r = client.post("/invoices", files={"file": ("big.pdf", big, "application/pdf")})
    assert r.status_code == 413