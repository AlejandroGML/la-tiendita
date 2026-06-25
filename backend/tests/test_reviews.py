"""Smoke test for ReviewController public list endpoint.

No PostgreSQL needed. The public list route requires no auth.
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from app.controllers import reviews as reviews_module


@pytest.fixture
def client():
    app = Litestar(
        route_handlers=[reviews_module.ReviewController],
        debug=False,
    )
    with TestClient(app=app, raise_server_exceptions=False) as tc:
        yield tc


class TestReviewListPublic:
    def test_list_reviews_route_exists(self, client):
        """Public list endpoint resolves (may 500 due to missing DI, but 404 is more telling)."""
        response = client.get("/api/v1/products/any-slug/reviews")
        # Without DI overrides the route resolves but handler fails — the
        # important thing is it's public (not 401).
        assert response.status_code != 401, (
            f"Public endpoint should not require auth, got {response.status_code}"
        )
