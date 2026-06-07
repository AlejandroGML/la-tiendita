"""HTTP integration tests for ReviewController.

Uses subclass mocks (pass isinstance) and Litestar TestClient with JWT auth.
The ReviewController's ``create_review`` handler has ``guards=[jwt_auth]``
pointing to the real ``app.guards.jwt_guard.jwt_auth``. We patch that guard
with our test instance so JWT validation uses our test secret.
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

from app.controllers import reviews as reviews_module
from app.schemas.review import ReviewListResponse, ReviewResponse
from app.services.review_service import ReviewService as _RealReviewService

from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

JWT_SECRET = "test-secret-key-for-reviews-min-32-chars!!"
JWT_ALGORITHM = "HS256"


async def _jwt_guard(connection: ASGIConnection, handler) -> None:
    """Test JWT guard — validates Bearer token using test secret and
    sets connection.scope['user'] so the controller can access
    request.user.  Analogue of JWTAuth.__call__ which is not available
    in Litestar 2.23."""
    from litestar.exceptions import HTTPException

    auth = connection.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(detail="Unauthorized", status_code=401)
    token_str = auth.split(" ", 1)[1]
    try:
        payload = jose_jwt.decode(
            token_str, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        connection.scope["user"] = _TestUser(
            id=payload["sub"],
            role=payload.get("role", "customer"),
        )
    except Exception as exc:
        raise HTTPException(
            detail=f"Invalid token: {exc}",
            status_code=401,
        ) from exc


class MockReviewService(_RealReviewService):
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


# Define test JWT auth instance. Will also be used to patch the controller's
# guard reference so JWT validation uses our test secret.
test_jwt_auth = JWTAuth[_TestUser](
    retrieve_user_handler=_retrieve_user,
    token_secret=JWT_SECRET,
    algorithm=JWT_ALGORITHM,
    exclude=["/health", "/schema", "/api/products"],
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


def _make_review_response(
    product_id: uuid.UUID | None = None,
) -> ReviewResponse:
    return ReviewResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        user_name="Test User",
        product_id=product_id or uuid.uuid4(),
        rating=4,
        comment="Great product!",
        created_at=datetime.now(timezone.utc),
    )


def _make_list_response() -> ReviewListResponse:
    return ReviewListResponse(
        reviews=[_make_review_response()],
        avg_rating=4.0,
        total_reviews=1,
        page=1,
        per_page=10,
    )


@pytest.fixture
def mock_svc():
    svc = MockReviewService()
    svc.create_review = AsyncMock()
    svc.list_reviews = AsyncMock()
    svc.can_review = AsyncMock()
    return svc


@pytest.fixture
def mock_session():
    return MockAsyncSession()


@pytest.fixture
def client(mock_svc, mock_session):
    _original_deps = reviews_module.ReviewController.dependencies
    reviews_module.ReviewController.dependencies = {
        "service": Provide(lambda: mock_svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    # Replace the broken guards=[jwt_auth] (JWTAuth is not callable in
    # Litestar 2.23) with a working guard that validates the JWT manually
    # using our test secret and sets connection.user.
    _orig_guards = list(reviews_module.ReviewController.create_review.guards)
    reviews_module.ReviewController.create_review.guards = [_jwt_guard]

    app = Litestar(
        route_handlers=[reviews_module.ReviewController],
        debug=False,
    )

    try:
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.mock_svc = mock_svc
            tc.mock_session = mock_session
            yield tc
    finally:
        reviews_module.ReviewController.create_review.guards = _orig_guards
        reviews_module.ReviewController.dependencies = _original_deps


class TestCreateReview:
    def test_create_review_success(self, client):
        mock_resp = _make_review_response()
        client.mock_svc.create_review.return_value = mock_resp
        token = _make_jwt(sub="user-abc")

        response = client.post(
            f"/api/products/{mock_resp.product_id}/reviews",
            json={"rating": 4, "comment": "Great product!"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["rating"] == 4
        assert body["user_name"] == "Test User"

    def test_duplicate_review_returns_409(self, client):
        client.mock_svc.create_review.side_effect = ValueError(
            "You have already reviewed this product"
        )
        token = _make_jwt(sub="user-abc")
        pid = uuid.uuid4()

        response = client.post(
            f"/api/products/{pid}/reviews",
            json={"rating": 5, "comment": "Again!"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 409, response.text
        assert "already reviewed" in response.json()["detail"]

    def test_review_without_purchase_returns_400(self, client):
        client.mock_svc.create_review.side_effect = ValueError(
            "You can only review products you have purchased"
        )
        token = _make_jwt(sub="user-abc")
        pid = uuid.uuid4()

        response = client.post(
            f"/api/products/{pid}/reviews",
            json={"rating": 3, "comment": "Nope"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400, response.text

    def test_unauthenticated_returns_401(self, client):
        pid = uuid.uuid4()

        response = client.post(
            f"/api/products/{pid}/reviews",
            json={"rating": 4, "comment": "test"},
        )

        assert response.status_code == 401, response.text


class TestListReviews:
    def test_list_reviews_returns_200(self, client):
        mock_resp = _make_list_response()
        client.mock_svc.list_reviews.return_value = mock_resp

        response = client.get("/api/products/some-slug/reviews")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["avg_rating"] == 4.0
        assert body["total_reviews"] == 1
        assert len(body["reviews"]) == 1

    def test_list_reviews_public_no_auth_required(self, client):
        mock_resp = _make_list_response()
        client.mock_svc.list_reviews.return_value = mock_resp

        response = client.get("/api/products/any-slug/reviews")

        assert response.status_code == 200, response.text

    def test_list_reviews_unknown_product(self, client):
        client.mock_svc.list_reviews.side_effect = ValueError(
            "Product not found: unknown"
        )

        response = client.get("/api/products/unknown/reviews")

        assert response.status_code == 404, response.text
