"""HTTP integration tests for PromotionController and AdminPromotionController.

Uses subclass mocks and Litestar TestClient with JWT auth.
AdminPromotionController has ``guards=[admin_guard]`` (a proper callable).
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth, Token
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.testing import TestClient
from sqlalchemy.ext.asyncio import AsyncSession as _RealAsyncSession

from app.controllers.promotions import AdminPromotionController, PromotionController
from app.schemas.promotion import (
    PromotionResponse,
    PromotionTranslationResponse,
)
from app.services.promotion_service import PromotionService as _RealPromotionService

from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

JWT_SECRET = "test-promo-secret-key-min-32-chars!!"
JWT_ALGORITHM = "HS256"


class MockPromotionService(_RealPromotionService):
    def __init__(self) -> None:
        pass


class MockAsyncSession(_RealAsyncSession):
    def __init__(self) -> None:
        pass


class _TestUser:
    def __init__(self, id: str, role: str = "customer") -> None:
        self.id = id
        self.role = role


async def _retrieve_user(
    token: Token, connection: ASGIConnection
) -> _TestUser | None:
    return _TestUser(id=token.sub, role=token.extras.get("role", "customer"))


test_jwt_auth = JWTAuth[_TestUser](
    retrieve_user_handler=_retrieve_user,
    token_secret=JWT_SECRET,
    algorithm=JWT_ALGORITHM,
    exclude=["/health", "/schema", "/api/promotions"],
)


def _make_jwt(sub: str, role: str = "customer") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_promotion_response() -> PromotionResponse:
    return PromotionResponse(
        id=uuid.uuid4(),
        code="SUMMER20",
        discount_percent=20,
        product_id=None,
        max_uses=100,
        current_uses=0,
        is_active=True,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        translations=[
            PromotionTranslationResponse(
                lang="es",
                title="Verano 20%",
                description="20% de descuento",
            ),
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_svc():
    svc = MockPromotionService()
    svc.list_active = AsyncMock()
    svc.get_all = AsyncMock()
    svc.get_by_id = AsyncMock()
    svc.create = AsyncMock()
    svc.update = AsyncMock()
    svc.delete = AsyncMock()
    return svc


@pytest.fixture
def mock_session():
    return MockAsyncSession()


@pytest.fixture
def client(mock_svc, mock_session):
    _orig_promo = PromotionController.dependencies
    _orig_admin = AdminPromotionController.dependencies

    PromotionController.dependencies = {
        "service": Provide(lambda: mock_svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }
    AdminPromotionController.dependencies = {
        "service": Provide(lambda: mock_svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    app = Litestar(
        route_handlers=[PromotionController, AdminPromotionController],
        on_app_init=[test_jwt_auth.on_app_init],
        debug=False,
    )

    try:
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.mock_svc = mock_svc
            tc.mock_session = mock_session
            yield tc
    finally:
        PromotionController.dependencies = _orig_promo
        AdminPromotionController.dependencies = _orig_admin


class TestPublicPromotions:
    def test_list_active_returns_200(self, client):
        mock_promo = _make_promotion_response()
        client.mock_svc.list_active.return_value = [mock_promo]

        response = client.get("/api/promotions/")

        assert response.status_code == 200, response.text
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1

    def test_list_active_public_no_auth(self, client):
        client.mock_svc.list_active.return_value = []

        response = client.get("/api/promotions/")

        assert response.status_code == 200, response.text


class TestAdminCreatePromotion:
    def test_create_returns_201(self, client):
        mock_resp = _make_promotion_response()
        client.mock_svc.create.return_value = mock_resp
        token = _make_jwt(sub="admin-1", role="admin")

        response = client.post(
            "/api/admin/promotions/",
            json={
                "code": "SUMMER20",
                "discount_percent": 20,
                "translations": [
                    {"language_code": "es", "title": "Verano 20%"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["code"] == "SUMMER20"

    def test_unauthenticated_returns_401(self, client):
        response = client.post(
            "/api/admin/promotions/",
            json={
                "code": "TEST",
                "discount_percent": 10,
                "translations": [
                    {"language_code": "es", "title": "Test"},
                ],
            },
        )
        assert response.status_code == 401, response.text

    def test_non_admin_returns_403(self, client):
        token = _make_jwt(sub="user-1", role="customer")
        client.mock_svc.create.return_value = _make_promotion_response()

        response = client.post(
            "/api/admin/promotions/",
            json={
                "code": "TEST",
                "discount_percent": 10,
                "translations": [
                    {"language_code": "es", "title": "Test"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403, response.text


class TestAdminListPromotions:
    def test_list_all_returns_200(self, client):
        client.mock_svc.get_all.return_value = ([_make_promotion_response()], 1)
        token = _make_jwt(sub="admin-1", role="admin")

        response = client.get(
            "/api/admin/promotions/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert "data" in body
        assert "pagination" in body


class TestAdminDeletePromotion:
    def test_delete_returns_204(self, client):
        client.mock_svc.delete.return_value = None
        pid = uuid.uuid4()
        token = _make_jwt(sub="admin-1", role="admin")

        response = client.delete(
            f"/api/admin/promotions/{pid}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204, response.text
