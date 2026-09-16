from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.trust import Trust


def test_trust_create_requires_authentication():
    client = TestClient(app)

    response = client.post(
        "/api/v1/trust",
        json={
            "name": "Test Trust",
            "code": "TEST001",
        },
    )

    assert response.status_code == 401


def test_trust_list_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/v1/trust")

    assert response.status_code == 401


def test_trust_get_requires_authentication():
    client = TestClient(app)

    response = client.get(f"/api/v1/trust/{uuid4()}")

    assert response.status_code == 401


def test_trust_update_requires_authentication():
    client = TestClient(app)

    response = client.patch(
        f"/api/v1/trust/{uuid4()}",
        json={"name": "Updated Trust"},
    )

    assert response.status_code == 401


def test_trust_response_model_data():
    trust = Trust(
        id=uuid4(),
        name="Memorial Trust",
        code="MEMORIAL",
        description="Test trust",
        is_active=True,
    )

    assert trust.name == "Memorial Trust"
    assert trust.code == "MEMORIAL"
    assert trust.is_active is True
