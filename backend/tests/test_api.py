from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_fake_pdf_is_rejected():
    with TestClient(app) as client:
        r = client.post("/invoices", files={"file": ("fake.pdf", b"this is not a pdf", "application/pdf")})
    assert r.status_code == 415


def test_oversized_file_is_rejected():
    big = b"%PDF" + b"0" * (10 * 1024 * 1024 + 10)
    with TestClient(app) as client:
        r = client.post("/invoices", files={"file": ("big.pdf", big, "application/pdf")})
    assert r.status_code == 413