"""Integration tests for AdminProductVariantController — variant CRUD endpoints.

Uses subclass-based mocks and JWTAuth guard test apps (same patterns
as test_admin.py and test_catalog.py). No PostgreSQL needed.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from litestar import Litestar
from litestar.contrib.jwt import JWTAuth
from litestar.di import Provide
from litestar.testing import TestClient

from tests.conftest import MockAsyncSession, TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET
from app.controllers.admin import AdminProductVariantController
from app.middleware.i18n import I18nMiddleware

# Ensure VariantService is resolvable in the admin module namespace for
# Litestar's get_type_hints() during controller dependency resolution.
import app.controllers.admin as _admin_mod
from app.services.variant_service import VariantService as _real_vs
_admin_mod.VariantService = _real_vs  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Subclass mock — MUST extend VariantService for msgspec type validation
# ---------------------------------------------------------------------------


class _MockVariantService(_real_vs):
    """VariantService subclass for test DI. Skips real __init__."""

    def __init__(self) -> None:
        self.list_variants = AsyncMock()
        self.create_variant = AsyncMock()
        self.update_variant = AsyncMock()
        self.delete_variant = AsyncMock()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _admin_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt_token('admin-1', 'admin')}"}


def _customer_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Fake variant model factory
# ---------------------------------------------------------------------------


class _FakeVariant:
    """Fake ProductVariant ORM object for model_validate.

    ``size`` is a plain string (not a FakeSize wrapper) because
    ProductVariantResponse.model_validate(..., from_attributes=True)
    extracts the attribute directly and expects str|None.
    """

    def __init__(
        self,
        variant_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        size: str | None = None,
        color: str | None = None,
        color_hex: str | None = None,
        stock: int = 10,
        sku: str = "HOOD-M-BLK-01",
    ):
        self.id = variant_id or uuid.uuid4()
        self.product_id = product_id or uuid.uuid4()
        self.size = size
        self.color = color
        self.color_hex = color_hex
        self.stock = stock
        self.sku = sku


def _make_fake_variant(**kwargs) -> _FakeVariant:
    return _FakeVariant(**kwargs)


# ---------------------------------------------------------------------------
# Shared client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """TestClient with mocked VariantService (variant methods only)."""
    svc = _MockVariantService()

    mock_session = MockAsyncSession()
    test_jwt_auth = JWTAuth[TestUser](
        retrieve_user_handler=_test_retrieve_user,
        token_secret=TOKEN_SECRET,
        algorithm="HS256",
        exclude=["/health", "/schema"],
    )

    _orig = AdminProductVariantController.dependencies
    AdminProductVariantController.dependencies = {
        "variant_service": Provide(lambda: svc, sync_to_thread=False),
        "session": Provide(lambda: mock_session, sync_to_thread=False),
    }

    app = Litestar(
        route_handlers=[AdminProductVariantController],
        on_app_init=[test_jwt_auth.on_app_init],
        middleware=[I18nMiddleware],
    )

    try:
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.mock_svc = svc
            tc.mock_session = mock_session
            yield tc
    finally:
        AdminProductVariantController.dependencies = _orig


# ---------------------------------------------------------------------------
# Auth guard tests
# ---------------------------------------------------------------------------


class TestVariantAuth:
    """Variant endpoints require admin JWT."""

    def test_list_variants_no_auth_401(self, client):
        pid = uuid.uuid4()
        r = client.get(f"/api/admin/products/{pid}/variants/")
        assert r.status_code == 401, r.text

    def test_list_variants_customer_403(self, client):
        pid = uuid.uuid4()
        r = client.get(
            f"/api/admin/products/{pid}/variants/",
            headers=_customer_headers(),
        )
        assert r.status_code == 403, r.text

    def test_create_variant_no_auth_401(self, client):
        pid = uuid.uuid4()
        r = client.post(f"/api/admin/products/{pid}/variants/", json={})
        assert r.status_code == 401, r.text

    def test_delete_variant_no_auth_401(self, client):
        pid = uuid.uuid4()
        vid = uuid.uuid4()
        r = client.delete(f"/api/admin/products/{pid}/variants/{vid}")
        assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# List variants
# ---------------------------------------------------------------------------


class TestListVariants:
    """GET /api/admin/products/{id}/variants — list non-deleted variants."""

    def test_list_variants_empty(self, client):
        """Returns empty data array when product has no variants."""
        pid = uuid.uuid4()
        client.mock_svc.list_variants.return_value = []

        r = client.get(
            f"/api/admin/products/{pid}/variants/",
            headers=_admin_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["data"] == []

    def test_list_variants_with_items(self, client):
        """Returns variant data with size, color, stock, sku."""
        pid = uuid.uuid4()
        v1 = _make_fake_variant(product_id=pid, size="M", color="Black", stock=10, sku="HOOD-M-BLK-01")
        v2 = _make_fake_variant(product_id=pid, size="L", color="White", stock=5, sku="HOOD-L-WHT-02")
        client.mock_svc.list_variants.return_value = [v1, v2]

        r = client.get(
            f"/api/admin/products/{pid}/variants/",
            headers=_admin_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["size"] == "M"
        assert body["data"][0]["color"] == "Black"
        assert body["data"][0]["stock"] == 10
        assert body["data"][0]["sku"] == "HOOD-M-BLK-01"
        assert body["data"][1]["size"] == "L"
        assert body["data"][1]["color"] == "White"

    def test_list_variants_product_not_found(self, client):
        """When product doesn't exist, returns 404."""
        pid = uuid.uuid4()
        client.mock_svc.list_variants.side_effect = ValueError("Product not found")

        r = client.get(
            f"/api/admin/products/{pid}/variants/",
            headers=_admin_headers(),
        )

        assert r.status_code == 404, r.text
        assert "not found" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Create variant
# ---------------------------------------------------------------------------


class TestCreateVariant:
    """POST /api/admin/products/{id}/variants — create a new variant."""

    def test_create_variant_minimal(self, client):
        """Create with stock=0 (default) and auto SKU."""
        pid = uuid.uuid4()
        v = _make_fake_variant(product_id=pid, stock=0, sku="HOOD-NS-NC-01")
        client.mock_svc.create_variant.return_value = v

        r = client.post(
            f"/api/admin/products/{pid}/variants/",
            json={},
            headers=_admin_headers(),
        )

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["stock"] == 0
        assert "id" in body
        assert "product_id" in body

    def test_create_variant_full(self, client):
        """Create with all fields set."""
        pid = uuid.uuid4()
        v = _make_fake_variant(
            product_id=pid,
            size="M",
            color="Azul",
            color_hex="#0000FF",
            stock=25,
            sku="HOOD-M-AZU-01",
        )
        client.mock_svc.create_variant.return_value = v

        r = client.post(
            f"/api/admin/products/{pid}/variants/",
            json={
                "size": "M",
                "color": "Azul",
                "color_hex": "#0000FF",
                "stock": 25,
                "sku": "HOOD-M-AZU-01",
            },
            headers=_admin_headers(),
        )

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["size"] == "M"
        assert body["color"] == "Azul"
        assert body["color_hex"] == "#0000FF"
        assert body["stock"] == 25
        assert body["sku"] == "HOOD-M-AZU-01"

    def test_create_variant_negative_stock_rejected(self, client):
        """Stock cannot be negative."""
        pid = uuid.uuid4()

        r = client.post(
            f"/api/admin/products/{pid}/variants/",
            json={"stock": -5},
            headers=_admin_headers(),
        )

        assert r.status_code == 400, r.text

    def test_create_variant_product_not_found(self, client):
        """When product doesn't exist, returns 400."""
        pid = uuid.uuid4()
        client.mock_svc.create_variant.side_effect = ValueError("Product not found")

        r = client.post(
            f"/api/admin/products/{pid}/variants/",
            json={"stock": 10},
            headers=_admin_headers(),
        )

        assert r.status_code == 400, r.text


# ---------------------------------------------------------------------------
# Update variant
# ---------------------------------------------------------------------------


class TestUpdateVariant:
    """PUT /api/admin/products/{id}/variants/{vid} — update a variant."""

    def test_update_variant_stock(self, client):
        """Update only the stock field."""
        pid = uuid.uuid4()
        vid = uuid.uuid4()
        v = _make_fake_variant(variant_id=vid, product_id=pid, stock=50)
        client.mock_svc.update_variant.return_value = v

        r = client.put(
            f"/api/admin/products/{pid}/variants/{vid}",
            json={"stock": 50},
            headers=_admin_headers(),
        )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["stock"] == 50
        assert body["id"] == str(vid)

    def test_update_variant_not_found(self, client):
        """Returns 404 when variant doesn't exist (controller checks for None)."""
        pid = uuid.uuid4()
        vid = uuid.uuid4()
        client.mock_svc.update_variant.return_value = None

        r = client.put(
            f"/api/admin/products/{pid}/variants/{vid}",
            json={"stock": 50},
            headers=_admin_headers(),
        )

        assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# Delete variant
# ---------------------------------------------------------------------------


class TestDeleteVariant:
    """DELETE /api/admin/products/{id}/variants/{vid} — soft-delete variant."""

    def test_delete_variant_success(self, client):
        """Soft-delete returns 204."""
        pid = uuid.uuid4()
        vid = uuid.uuid4()
        client.mock_svc.delete_variant.return_value = True

        r = client.delete(
            f"/api/admin/products/{pid}/variants/{vid}",
            headers=_admin_headers(),
        )

        assert r.status_code == 204, r.text

    def test_delete_variant_not_found(self, client):
        """Returns 400 when variant doesn't exist (controller raises ValidationException)."""
        pid = uuid.uuid4()
        vid = uuid.uuid4()
        client.mock_svc.delete_variant.side_effect = ValueError("Variant not found")

        r = client.delete(
            f"/api/admin/products/{pid}/variants/{vid}",
            headers=_admin_headers(),
        )

        assert r.status_code == 400, r.text

    def test_delete_variant_in_cart_blocked(self, client):
        """Returns 400 when variant is referenced by active cart items."""
        pid = uuid.uuid4()
        vid = uuid.uuid4()
        client.mock_svc.delete_variant.side_effect = ValueError(
            "Cannot delete variant: referenced by 3 active cart items"
        )

        r = client.delete(
            f"/api/admin/products/{pid}/variants/{vid}",
            headers=_admin_headers(),
        )

        assert r.status_code == 400, r.text
        assert "active cart" in r.json()["detail"]


# ---------------------------------------------------------------------------
# SKU generation unit tests
# ---------------------------------------------------------------------------


class TestSkuGeneration:
    """Unit tests for SKU auto-generation helpers in VariantService.

    Tests the real static/async helpers directly — no DB needed for
    the static helpers; the async SKU generator is tested with a
    mock session.
    """

    def test_color_abbreviation(self):
        """_color_abbr returns 2-char uppercase abbreviation."""
        from app.services.variant_service import VariantService

        assert VariantService._color_abbr("Black") == "BL"
        assert VariantService._color_abbr("Red") == "RE"
        assert VariantService._color_abbr("Azul") == "AZ"

    def test_color_abbreviation_multi_word(self):
        """Multi-word colors take first letter of each word."""
        from app.services.variant_service import VariantService

        assert VariantService._color_abbr("Light Blue") == "LB"

    def test_color_abbreviation_none(self):
        """None or empty color returns None (_generate_variant_sku replaces with 'NC')."""
        from app.services.variant_service import VariantService

        assert VariantService._color_abbr(None) is None
        assert VariantService._color_abbr("") is None

    def test_sku_slug_prefix(self):
        """_sku_slug_prefix returns uppercase prefix from slug."""
        from app.services.variant_service import VariantService

        assert VariantService._sku_slug_prefix("hoodie") == "HOOD"
        assert VariantService._sku_slug_prefix("ab") == "AB"
        # Multi-word slug: takes first letter of up to 3 parts
        assert VariantService._sku_slug_prefix("denim-jacket") == "DJ"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_basic(self):
        """_generate_variant_sku returns expected format."""
        from app.services.variant_service import VariantService

        svc = VariantService()
        mock_session = MockAsyncSession()
        # No collision → returns seq 01
        mock_session.scalar = AsyncMock(return_value=None)

        sku = await svc._generate_variant_sku(mock_session, "hoodie", "M", "BL")
        assert sku == "HOOD-M-BL-01"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_no_size(self):
        """Null size uses 'NS' (No Size)."""
        from app.services.variant_service import VariantService

        svc = VariantService()
        mock_session = MockAsyncSession()
        mock_session.scalar = AsyncMock(return_value=None)

        sku = await svc._generate_variant_sku(mock_session, "hoodie", None, "RE")
        assert sku == "HOOD-NS-RE-01"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_no_color(self):
        """Null color uses 'NC' (No Color)."""
        from app.services.variant_service import VariantService

        svc = VariantService()
        mock_session = MockAsyncSession()
        mock_session.scalar = AsyncMock(return_value=None)

        sku = await svc._generate_variant_sku(mock_session, "hoodie", "M", None)
        assert sku == "HOOD-M-NC-01"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_collision_increments_seq(self):
        """When SKU exists, seq increments until a free one is found."""
        from app.services.variant_service import VariantService

        svc = VariantService()
        mock_session = MockAsyncSession()
        # First two calls simulate collisions, third is free
        mock_session.scalar = AsyncMock(side_effect=[True, True, None])

        sku = await svc._generate_variant_sku(mock_session, "hoodie", "M", "BL")
        assert sku == "HOOD-M-BL-03"
