from fastapi.testclient import TestClient

from app.main import app

PASSWORD = "correct-horse-battery"


def login(email, password=PASSWORD):
    client = TestClient(app)
    response = client.post("/auth/login", json={"email": email, "password": password})
    return client, response