from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.trust import Trust
from app.models.user import User


TRUST_ID = uuid4()
OTHER_TRUST_ID = uuid4()
USER_ID = uuid4()
ROLE_ID = uuid4()


def make_user(*, trust_id=None):
    return User(
        id=USER_ID,
        trust_id=trust_id,
        role_id=ROLE_ID,
        email="admin@example.com",
        password_hash="unused",
        full_name="Test Admin",
        is_active=True,
        is_verified=True,
    )


def make_trust(*, trust_id=TRUST_ID, name="Memorial Trust", code="MEMORIAL"):
    return Trust(
        id=trust_id,
        name=name,
        code=code,
        description="Test trust",
        is_active=True,
    )


def setup_client(user):
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app), db


def teardown_client():
    app.dependency_overrides.clear()


def test_super_admin_can_create_trust():
    client, _ = setup_client(make_user())

    try:
        trust = make_trust()

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.create",
            return_value=trust,
        ) as create_mock:
            response = client.post(
                "/api/v1/trust",
                json={
                    "name": trust.name,
                    "code": trust.code,
                    "description": trust.description,
                },
            )

        assert response.status_code == 201
        assert response.json()["code"] == "MEMORIAL"
        create_mock.assert_called_once()

    finally:
        teardown_client()


def test_trust_admin_can_read_own_trust():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        trust = make_trust()

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.get_by_id",
            return_value=trust,
        ), patch(
            "app.api.v1.trust.has_trust_access",
            return_value=True,
        ):
            response = client.get(f"/api/v1/trust/{TRUST_ID}")

        assert response.status_code == 200
        assert response.json()["id"] == str(TRUST_ID)

    finally:
        teardown_client()


def test_trust_admin_cannot_read_other_trust():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        trust = make_trust(
            trust_id=OTHER_TRUST_ID,
            name="Other Trust",
            code="OTHER",
        )

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.get_by_id",
            return_value=trust,
        ), patch(
            "app.api.v1.trust.has_trust_access",
            return_value=False,
        ):
            response = client.get(f"/api/v1/trust/{OTHER_TRUST_ID}")

        assert response.status_code == 403

    finally:
        teardown_client()


def test_missing_permission_returns_403():
    client, _ = setup_client(make_user())

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.get("/api/v1/trust")

        assert response.status_code == 403

    finally:
        teardown_client()


def test_duplicate_trust_code_returns_409():
    client, _ = setup_client(make_user())

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.create",
            side_effect=ValueError(
                "A trust with this code already exists."
            ),
        ):
            response = client.post(
                "/api/v1/trust",
                json={
                    "name": "Duplicate Trust",
                    "code": "MEMORIAL",
                },
            )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    finally:
        teardown_client()


def test_unknown_trust_returns_404():
    client, _ = setup_client(make_user())

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.get_by_id",
            return_value=None,
        ):
            response = client.get(f"/api/v1/trust/{uuid4()}")

        assert response.status_code == 404

    finally:
        teardown_client()


def test_trust_update_requires_update_permission():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.patch(
                f"/api/v1/trust/{TRUST_ID}",
                json={"name": "Updated Trust"},
            )

        assert response.status_code == 403

    finally:
        teardown_client()


def test_trust_admin_can_update_own_trust():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        updated = make_trust(name="Updated Trust")

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.get_by_id",
            return_value=make_trust(),
        ), patch(
            "app.api.v1.trust.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.trust.TrustService.update",
            return_value=updated,
        ):
            response = client.patch(
                f"/api/v1/trust/{TRUST_ID}",
                json={"name": "Updated Trust"},
            )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Trust"

    finally:
        teardown_client()
