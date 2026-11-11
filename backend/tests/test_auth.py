import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import InvoiceRecord, SessionLocal
from app.main import app
from tests.helpers import PASSWORD, login

PNG = b"\x89PNG\r\n\x1a\n"


def invoice_id():
    with SessionLocal() as db:
        return db.scalar(select(InvoiceRecord.id).limit(1))


def test_requests_without_login_are_rejected():
    client = TestClient(app)
    assert client.get("/invoices").status_code == 401
    assert client.get("/audit").status_code == 401
    r = client.post("/invoices", files={"file": ("a.png", PNG, "image/png")})
    assert r.status_code == 401


def test_forged_and_garbage_tokens_are_rejected():
    client = TestClient(app)
    wrong_key = jwt.encode(
        {"sub": "1", "exp": 9999999999}, "wrong-secret-" + "y" * 40, algorithm="HS256"
    )
    no_signature = jwt.encode({"sub": "1", "exp": 9999999999}, None, algorithm="none")
    for token in (wrong_key, no_signature, "garbage"):
        client.cookies.set("access_token", token)
        assert client.get("/invoices").status_code == 401


def test_login_sets_httponly_strict_cookie():
    _, r = login("admin@a.test")
    assert r.status_code == 200
    header = r.headers["set-cookie"].lower()
    assert "httponly" in header
    assert "samesite=strict" in header


def test_unknown_user_and_wrong_password_look_identical():
    _, r1 = login("nobody@a.test", "some-wrong-password")
    _, r2 = login("viewer@a.test", "some-wrong-password")
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


def test_account_locks_after_repeated_failures():
    for _ in range(5):
        _, r = login("lock@a.test", "some-wrong-password")
        assert r.status_code == 401
    _, r = login("lock@a.test")
    assert r.status_code == 429


def test_viewer_cannot_upload_edit_or_manage():
    client, r = login("viewer@a.test")
    assert r.status_code == 200
    assert client.get("/invoices").status_code == 200
    up = client.post("/invoices", files={"file": ("a.png", PNG, "image/png")})
    assert up.status_code == 403
    assert client.patch(f"/invoices/{invoice_id()}", json={"approve": True}).status_code == 403
    new = {"email": "x@a.test", "password": "long-enough-password", "role": "admin"}
    assert client.post("/users", json=new).status_code == 403
    assert client.get("/audit").status_code == 403


def test_other_company_cannot_see_or_change_invoice():
    inv = invoice_id()
    other, _ = login("admin@b.test")
    assert other.get(f"/invoices/{inv}").status_code == 404
    assert other.patch(f"/invoices/{inv}", json={"approve": True}).status_code == 404
    assert other.get("/invoices").json() == []
    owner, _ = login("admin@a.test")
    assert owner.get(f"/invoices/{inv}").status_code == 200


def test_weak_password_and_bad_role_are_rejected():
    client, _ = login("admin@a.test")
    weak = {"email": "n1@a.test", "password": "short", "role": "viewer"}
    assert client.post("/users", json=weak).status_code == 422
    bad_role = {"email": "n2@a.test", "password": "long-enough-password", "role": "root"}
    assert client.post("/users", json=bad_role).status_code == 422


def test_audit_log_is_company_scoped_and_hides_secrets():
    admin_a, _ = login("admin@a.test")
    r = admin_a.get("/audit")
    assert r.status_code == 200
    assert "login" in {row["action"] for row in r.json()}
    assert PASSWORD not in r.text
    admin_b, _ = login("admin@b.test")
    rows_b = admin_b.get("/audit").json()
    assert rows_b
    assert all(row["email"].endswith("@b.test") for row in rows_b)