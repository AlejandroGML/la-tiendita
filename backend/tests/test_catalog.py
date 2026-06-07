"""Integration tests for product catalog API — controllers, guards, pagination.

Uses Litestar TestClient with subclass mocks and dedicated test apps.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from litestar import Litestar, get
from litestar.contrib.jwt import JWTAuth
from litestar.di import Provide
from litestar.testing import TestClient

from tests.conftest import TestUser, _test_retrieve_user, make_jwt_token, TOKEN_SECRET

from app.controllers.categories import AdminCategoryController, CategoryController
from app.controllers.products import AdminProductController, ProductController
from app.controllers.upload import UploadController
from app.guards.admin_guard import admin_guard
from app.middleware.i18n import I18nMiddleware


# ---------------------------------------------------------------------------
# Fake model factories
# ---------------------------------------------------------------------------


class _FakeTranslation:
    def __init__(self, language_code: str, name: str, description: str | None = None):
        self.language_code = language_code
        self.name = name
        self.description = description


class _FakeCategoryTrans:
    def __init__(self, language_code: str, name: str):
        self.language_code = language_code
        self.name = name


class _FakeCategory:
    def __init__(self, id: int, slug: str, translations: list):
        self.id = id
        self.slug = slug
        self.image_url = None
        self.translations = translations


class _FakeProduct:
    def __init__(
        self,
        product_id: uuid.UUID,
        slug: str,
        price: Decimal,
        category_id: int | None = None,
        size=None,
        brand: str | None = None,
        condition=None,
        condition_rating: int | None = None,
        condition_details: dict | None = None,
        target_gender: str | None = None,
        material: str | None = None,
        colors: list | None = None,
        trend: str | None = None,
        pattern: str | None = None,
        season: str | None = None,
        cut: list | None = None,
        usage: str | None = None,
        source_dataset: str | None = None,
        image_urls=None,
        stock: int = 1,
        translations=None,
        created_at: datetime | None = None,
        category=None,
    ):
        self.id = product_id
        self.slug = slug
        self.price = price
        self.category_id = category_id
        self.size = size
        self.brand = brand
        self.condition = condition
        self.condition_rating = condition_rating
        self.condition_details = condition_details
        self.target_gender = target_gender
        self.material = material
        self.colors = colors
        self.trend = trend
        self.pattern = pattern
        self.season = season
        self.cut = cut
        self.usage = usage
        self.source_dataset = source_dataset
        self.image_urls = image_urls or []
        self.stock = stock
        self.translations = translations or []
        self.created_at = created_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.category = category
        self.deleted_at = None


def _make_fake_product(
    slug="chaqueta-denim",
    price=Decimal("29.99"),
    category_id=1,
    translations=None,
    product_id=None,
    size=None,
    condition=None,
) -> _FakeProduct:
    from app.models.product import ProductCondition, ProductSize

    return _FakeProduct(
        product_id=product_id or uuid.uuid4(),
        slug=slug,
        price=price,
        category_id=category_id,
        size=ProductSize.M if size is None else size,
        brand="Levi's",
        condition=ProductCondition.GOOD if condition is None else condition,
        translations=translations
        or [
            _FakeTranslation("es", "Chaqueta Denim", "Chaqueta de mezclilla azul"),
            _FakeTranslation("en", "Denim Jacket", "Blue denim jacket"),
            _FakeTranslation("sv", "Denimjacka", "Blå denimjacka"),
        ],
        category=_FakeCategory(
            id=1,
            slug="chaquetas",
            translations=[
                _FakeCategoryTrans("es", "Chaquetas"),
                _FakeCategoryTrans("en", "Jackets"),
            ],
        ),
    )


def _make_fake_category(cat_id=1, slug="chaquetas", translations=None):
    return _FakeCategory(
        id=cat_id,
        slug=slug,
        translations=translations
        or [
            _FakeCategoryTrans("es", "Chaquetas"),
            _FakeCategoryTrans("en", "Jackets"),
        ],
    )


# ---------------------------------------------------------------------------
# Session mock
# ---------------------------------------------------------------------------


def _make_mock_session():
    """Create an AsyncSession mock that supports async context manager."""
    from sqlalchemy.ext.asyncio import AsyncSession

    mock = MagicMock(spec=AsyncSession)
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    mock.execute = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    mock.delete = AsyncMock()
    return mock


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _make_test_jwt_auth(exclude: list | None = None) -> JWTAuth:
    return JWTAuth[TestUser](
        retrieve_user_handler=_test_retrieve_user,
        token_secret=TOKEN_SECRET,
        algorithm="HS256",
        exclude=exclude or ["/health", "/schema", "/api/products", "/api/categories", "/uploads/"],
    )


def _admin_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt_token('admin-1', 'admin')}"}


def _customer_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt_token('customer-1', 'customer')}"}


# ---------------------------------------------------------------------------
# Public product catalog tests
# ---------------------------------------------------------------------------


class TestProductCatalog:
    """Integration tests for GET /api/products (public)."""

    @pytest.fixture
    def client(self):
        from app.services.product_service import ProductService

        svc = MagicMock(spec=ProductService)
        svc.list_products = AsyncMock()
        svc.get_product_by_slug = AsyncMock()

        mock_session = _make_mock_session()

        _orig = ProductController.dependencies
        ProductController.dependencies = {
            "service": Provide(lambda: svc, sync_to_thread=False),
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[ProductController],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_svc = svc
                tc.mock_session = mock_session
                yield tc
        finally:
            ProductController.dependencies = _orig

    def test_list_products_returns_paginated_data(self, client):
        p1 = _make_fake_product(slug="p1", price=Decimal("10.00"))
        p2 = _make_fake_product(slug="p2", price=Decimal("20.00"))
        client.mock_svc.list_products.return_value = ([p1, p2], 2)

        r = client.get("/api/products/")
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["data"]) == 2
        assert body["pagination"]["total"] == 2
        assert body["pagination"]["pages"] == 1
        assert "lang" in body["meta"]

    def test_list_products_with_pagination_params(self, client):
        client.mock_svc.list_products.return_value = ([_make_fake_product()], 50)
        r = client.get("/api/products/?page=2&per_page=5")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["pagination"]["page"] == 2
        assert body["pagination"]["per_page"] == 5
        assert body["pagination"]["total"] == 50

    def test_list_products_invalid_page_returns_400(self, client):
        r = client.get("/api/products/?page=-1")
        assert r.status_code == 400, r.text

    def test_list_products_per_page_exceeds_limit_returns_400(self, client):
        r = client.get("/api/products/?per_page=200")
        assert r.status_code == 400, r.text

    def test_list_products_with_lang_param(self, client):
        client.mock_svc.list_products.return_value = ([_make_fake_product()], 1)
        r = client.get("/api/products/?lang=sv")
        assert r.status_code == 200, r.text
        t = r.json()["data"][0]["translations"][0]
        assert t["language_code"] == "sv"
        assert t["name"] == "Denimjacka"

    def test_list_products_translation_fallback_to_en(self, client):
        p = _make_fake_product(translations=[
            _FakeTranslation("es", "Chaqueta Denim", "Azul"),
            _FakeTranslation("en", "Denim Jacket", "Blue"),
        ])
        client.mock_svc.list_products.return_value = ([p], 1)
        r = client.get("/api/products/?lang=sv")
        assert r.status_code == 200, r.text
        t = r.json()["data"][0]["translations"][0]
        assert t["language_code"] == "en"
        assert t["name"] == "Denim Jacket"

    def test_list_products_with_filters(self, client):
        client.mock_svc.list_products.return_value = ([], 0)
        r = client.get("/api/products/?category_id=3&min_price=10&max_price=50&size=M")
        assert r.status_code == 200, r.text
        meta = r.json()["meta"]
        assert meta["category_id"] == 3
        assert meta["size"] == "M"
        assert len(r.json()["data"]) == 0

    def test_get_product_by_slug_returns_detail(self, client):
        client.mock_svc.get_product_by_slug.return_value = _make_fake_product()
        r = client.get("/api/products/chaqueta-denim")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["slug"] == "chaqueta-denim"
        assert len(body["translations"]) == 3

    def test_get_product_by_slug_404(self, client):
        client.mock_svc.get_product_by_slug.return_value = None
        r = client.get("/api/products/nonexistent")
        assert r.status_code == 404, r.text

    def test_get_product_by_uuid_redirects_to_slug(self, client):
        pid = uuid.UUID("12345678-1234-1234-1234-123456789abc")
        p1 = _make_fake_product(product_id=pid)
        client.mock_svc.get_product_by_slug.return_value = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = p1
        client.mock_session.execute.return_value = mock_result

        r = client.get(f"/api/products/{pid}", follow_redirects=False)
        assert r.status_code in (307, 302), f"Expected redirect, got {r.status_code}"

    def test_list_products_public_no_auth_required(self, client):
        client.mock_svc.list_products.return_value = ([], 0)
        r = client.get("/api/products/")
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Admin product tests
# ---------------------------------------------------------------------------


class TestAdminProducts:
    """Integration tests for POST/PUT/DELETE /api/admin/products."""

    @pytest.fixture
    def client(self):
        from app.services.product_service import ProductService

        svc = MagicMock(spec=ProductService)
        svc.create_product = AsyncMock()
        svc.update_product = AsyncMock()
        svc.delete_product = AsyncMock()

        mock_session = _make_mock_session()
        test_jwt_auth = _make_test_jwt_auth()

        _orig = AdminProductController.dependencies
        AdminProductController.dependencies = {
            "service": Provide(lambda: svc, sync_to_thread=False),
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[AdminProductController],
            on_app_init=[test_jwt_auth.on_app_init],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_svc = svc
                tc.mock_session = mock_session
                yield tc
        finally:
            AdminProductController.dependencies = _orig

    def test_create_product_no_auth_401(self, client):
        r = client.post("/api/admin/products/", json={
            "translations": [{"language_code": "es", "name": "Test"}],
            "price": "10.00",
        })
        assert r.status_code == 401, r.text

    def test_create_product_customer_403(self, client):
        r = client.post(
            "/api/admin/products/",
            json={"translations": [{"language_code": "es", "name": "Test"}], "price": "10.00"},
            headers=_customer_headers(),
        )
        assert r.status_code == 403, r.text

    def test_create_product_admin_201(self, client):
        client.mock_svc.create_product.return_value = _make_fake_product()
        r = client.post(
            "/api/admin/products/",
            json={
                "translations": [{"language_code": "es", "name": "Chaqueta Denim", "description": "Azul"}],
                "price": "29.99",
                "category_id": 1,
            },
            headers=_admin_headers(),
        )
        assert r.status_code == 201, r.text
        assert r.json()["slug"] == "chaqueta-denim"

    def test_create_product_no_translations_400(self, client):
        r = client.post(
            "/api/admin/products/",
            json={"translations": [], "price": "10.00"},
            headers=_admin_headers(),
        )
        assert r.status_code == 400, r.text

    def test_update_product_admin_200(self, client):
        client.mock_svc.update_product.return_value = _make_fake_product()
        pid = str(uuid.uuid4())
        r = client.put(
            f"/api/admin/products/{pid}",
            json={"price": "39.99"},
            headers=_admin_headers(),
        )
        assert r.status_code == 200, r.text

    def test_update_product_not_found_404(self, client):
        client.mock_svc.update_product.return_value = None
        pid = str(uuid.uuid4())
        r = client.put(
            f"/api/admin/products/{pid}",
            json={"price": "39.99"},
            headers=_admin_headers(),
        )
        assert r.status_code == 404, r.text

    def test_delete_product_admin_204(self, client):
        client.mock_svc.delete_product.return_value = True
        pid = str(uuid.uuid4())
        r = client.delete(f"/api/admin/products/{pid}", headers=_admin_headers())
        assert r.status_code == 204, r.text

    def test_delete_product_not_found_404(self, client):
        client.mock_svc.delete_product.return_value = False
        pid = str(uuid.uuid4())
        r = client.delete(f"/api/admin/products/{pid}", headers=_admin_headers())
        assert r.status_code == 404, r.text

    def test_update_product_no_auth_401(self, client):
        r = client.put(f"/api/admin/products/{uuid.uuid4()}", json={"price": "39.99"})
        assert r.status_code == 401, r.text

    def test_delete_product_no_auth_401(self, client):
        r = client.delete(f"/api/admin/products/{uuid.uuid4()}")
        assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# Public category tests
# ---------------------------------------------------------------------------


class TestCategoryCatalog:
    """Integration tests for GET /api/categories (public)."""

    @pytest.fixture
    def client(self):
        mock_session = _make_mock_session()

        _orig = CategoryController.dependencies
        CategoryController.dependencies = {
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[CategoryController],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_session = mock_session
                yield tc
        finally:
            CategoryController.dependencies = _orig

    def _mock_result(self, mock_session, categories):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = categories
        mock_session.execute.return_value = mock_result

    def test_list_categories_returns_translated_names(self, client):
        cats = [_make_fake_category(1, "chaquetas"), _make_fake_category(2, "pantalones")]
        self._mock_result(client.mock_session, cats)
        r = client.get("/api/categories/?lang=es")
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body) == 2
        assert body[0]["name"] == "Chaquetas"

    def test_list_categories_fallback_to_en(self, client):
        cats = [_make_fake_category(1, "test", translations=[
            _FakeCategoryTrans("es", "Prueba"),
            _FakeCategoryTrans("en", "Test"),
        ])]
        self._mock_result(client.mock_session, cats)
        r = client.get("/api/categories/?lang=sv")
        assert r.status_code == 200, r.text
        assert r.json()[0]["name"] == "Test"

    def test_list_categories_default_lang_es(self, client):
        cats = [_make_fake_category()]
        self._mock_result(client.mock_session, cats)
        r = client.get("/api/categories/")
        assert r.status_code == 200, r.text
        assert r.json()[0]["name"] == "Chaquetas"


# ---------------------------------------------------------------------------
# Admin category tests
# ---------------------------------------------------------------------------


class TestAdminCategories:
    """Integration tests for POST/PUT/DELETE /api/admin/categories."""

    @pytest.fixture
    def client(self):
        mock_session = _make_mock_session()
        test_jwt_auth = _make_test_jwt_auth()

        _orig = AdminCategoryController.dependencies
        AdminCategoryController.dependencies = {
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(
            route_handlers=[AdminCategoryController],
            on_app_init=[test_jwt_auth.on_app_init],
            middleware=[I18nMiddleware],
        )

        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_session = mock_session
                yield tc
        finally:
            AdminCategoryController.dependencies = _orig

    def test_create_category_no_auth_401(self, client):
        r = client.post("/api/admin/categories/", json={
            "slug": "test",
            "translations": [{"language_code": "es", "name": "Test"}],
        })
        assert r.status_code == 401, r.text

    def test_create_category_customer_403(self, client):
        r = client.post(
            "/api/admin/categories/",
            json={"slug": "test", "translations": [{"language_code": "es", "name": "Test"}]},
            headers=_customer_headers(),
        )
        assert r.status_code == 403, r.text

    def test_delete_category_no_auth_401(self, client):
        r = client.delete("/api/admin/categories/1")
        assert r.status_code == 401, r.text

    def test_delete_category_customer_403(self, client):
        r = client.delete("/api/admin/categories/1", headers=_customer_headers())
        assert r.status_code == 403, r.text

    def test_create_category_admin_201(self, client):
        slug_check = MagicMock()
        slug_check.scalar_one_or_none.return_value = None

        reload_result = MagicMock()
        cat = _make_fake_category(1, "chaquetas")
        reload_result.scalar_one.return_value = cat

        client.mock_session.execute = AsyncMock(side_effect=[slug_check, reload_result])

        r = client.post(
            "/api/admin/categories/",
            json={
                "slug": "chaquetas",
                "translations": [
                    {"language_code": "es", "name": "Chaquetas"},
                    {"language_code": "en", "name": "Jackets"},
                ],
            },
            headers=_admin_headers(),
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["slug"] == "chaquetas"
        assert len(body["translations"]) == 2

    def test_create_category_duplicate_slug_409(self, client):
        slug_check = MagicMock()
        slug_check.scalar_one_or_none.return_value = 1
        client.mock_session.execute = AsyncMock(return_value=slug_check)

        r = client.post(
            "/api/admin/categories/",
            json={"slug": "chaquetas", "translations": [{"language_code": "es", "name": "Chaquetas"}]},
            headers=_admin_headers(),
        )
        assert r.status_code == 409, r.text
        assert "already exists" in r.json()["detail"]


# ---------------------------------------------------------------------------
# Upload controller tests
# ---------------------------------------------------------------------------


class TestUpload:
    """Integration tests for POST /api/upload (admin-only)."""

    @pytest.fixture
    def client(self, tmp_path):
        test_jwt_auth = _make_test_jwt_auth()

        app = Litestar(
            route_handlers=[UploadController],
            on_app_init=[test_jwt_auth.on_app_init],
            middleware=[I18nMiddleware],
        )

        with TestClient(app=app, raise_server_exceptions=False) as tc:
            tc.upload_dir = tmp_path
            yield tc

    @staticmethod
    def _fake_jpeg_bytes() -> bytes:
        from io import BytesIO
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def test_upload_no_auth_401(self, client):
        r = client.post("/api/upload")
        assert r.status_code == 401, r.text

    def test_upload_customer_403(self, client):
        r = client.post(
            "/api/upload",
            files={"data": ("test.jpg", self._fake_jpeg_bytes(), "image/jpeg")},
            headers=_customer_headers(),
        )
        assert r.status_code == 403, r.text

    def test_upload_invalid_mime_400(self, client):
        r = client.post(
            "/api/upload",
            files={"data": ("test.gif", b"GIF89a...", "image/gif")},
            headers=_admin_headers(),
        )
        assert r.status_code == 400, r.text
        assert "unsupported file type" in r.json()["detail"].lower()

    def test_upload_file_too_large_400(self, client):
        large_data = b"x" * (5 * 1024 * 1024 + 1)
        r = client.post(
            "/api/upload",
            files={"data": ("large.jpg", large_data, "image/jpeg")},
            headers=_admin_headers(),
        )
        assert r.status_code == 400, r.text
        assert "exceeds maximum size" in r.json()["detail"]

    @patch("app.controllers.upload.resize_image")
    @patch("app.controllers.upload.generate_thumbnail")
    @patch("app.controllers.upload.os.makedirs")
    @patch("app.controllers.upload.settings")
    def test_upload_success_201(
        self, mock_settings, mock_makedirs, mock_thumb, mock_resize, client
    ):
        mock_settings.UPLOAD_DIR = str(client.upload_dir)
        mock_settings.MAX_IMAGE_SIZE = 5 * 1024 * 1024
        mock_resize.return_value = str(client.upload_dir / "abc.jpg")
        mock_thumb.return_value = str(client.upload_dir / "abc_thumb.webp")

        r = client.post(
            "/api/upload",
            files={"data": ("test.jpg", self._fake_jpeg_bytes(), "image/jpeg")},
            headers=_admin_headers(),
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert "image_url" in body
        assert "thumbnail_url" in body
        assert body["image_url"].startswith("/uploads/")


# ---------------------------------------------------------------------------
# Guard contract tests
# ---------------------------------------------------------------------------


class TestGuardContract:
    """Verify admin guards work correctly in isolation."""

    def test_unauthenticated_gets_401(self) -> None:
        ta = _make_test_jwt_auth()
        @get("/test-guarded", guards=[admin_guard], sync_to_thread=False)
        async def guarded() -> dict:
            return {"ok": True}
        app = Litestar(route_handlers=[guarded], on_app_init=[ta.on_app_init])
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            assert tc.get("/test-guarded").status_code == 401

    def test_customer_gets_403(self) -> None:
        ta = _make_test_jwt_auth()
        @get("/test-guarded", guards=[admin_guard], sync_to_thread=False)
        async def guarded() -> dict:
            return {"ok": True}
        app = Litestar(route_handlers=[guarded], on_app_init=[ta.on_app_init])
        tok = make_jwt_token("c1", "customer")
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            r = tc.get("/test-guarded", headers={"Authorization": f"Bearer {tok}"})
            assert r.status_code == 403, r.text

    def test_admin_gets_200(self) -> None:
        ta = _make_test_jwt_auth()
        @get("/test-guarded", guards=[admin_guard], sync_to_thread=False)
        async def guarded() -> dict:
            return {"ok": True}
        app = Litestar(route_handlers=[guarded], on_app_init=[ta.on_app_init])
        tok = make_jwt_token("admin-1", "admin")
        with TestClient(app=app, raise_server_exceptions=False) as tc:
            r = tc.get("/test-guarded", headers={"Authorization": f"Bearer {tok}"})
            assert r.status_code == 200, r.text
            assert r.json()["ok"] is True


# ---------------------------------------------------------------------------
# Search and empty results
# ---------------------------------------------------------------------------


class TestSearchAndEmptyResults:
    """Additional edge-case tests."""

    @pytest.fixture
    def client(self):
        from app.services.product_service import ProductService

        svc = MagicMock(spec=ProductService)
        svc.list_products = AsyncMock()

        mock_session = _make_mock_session()

        _orig = ProductController.dependencies
        ProductController.dependencies = {
            "service": Provide(lambda: svc, sync_to_thread=False),
            "session": Provide(lambda: mock_session, sync_to_thread=False),
        }

        app = Litestar(route_handlers=[ProductController], middleware=[I18nMiddleware])
        try:
            with TestClient(app=app, raise_server_exceptions=False) as tc:
                tc.mock_svc = svc
                yield tc
        finally:
            ProductController.dependencies = _orig

    def test_empty_result_set_returns_200(self, client):
        client.mock_svc.list_products.return_value = ([], 0)
        r = client.get("/api/products/?search=nonexistent")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["data"] == []
        assert body["pagination"]["total"] == 0

    def test_search_filter_passed_to_service(self, client):
        client.mock_svc.list_products.return_value = ([], 0)
        r = client.get("/api/products/?search=denim&lang=es")
        assert r.status_code == 200, r.text
        assert r.json()["meta"]["search"] == "denim"
        assert r.json()["meta"]["lang"] == "es"
