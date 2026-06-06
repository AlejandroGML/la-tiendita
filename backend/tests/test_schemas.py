"""Tests for Pydantic v2 schema validation (ProductFilter, CreateProductRequest, etc.)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError


class TestProductFilter:
    """Validation of public catalog query parameters."""

    @pytest.fixture(autouse=True)
    def _schema(self):
        from app.schemas.common import ProductFilter

        self.ProductFilter = ProductFilter

    def test_defaults(self):
        """Default page=1, per_page=12, lang=es."""
        f = self.ProductFilter()
        assert f.page == 1
        assert f.per_page == 12
        assert f.lang == "es"
        assert f.category is None
        assert f.q is None

    def test_valid_full_filter(self):
        """All optional fields can be set."""
        f = self.ProductFilter(
            page=2,
            per_page=24,
            lang="sv",
            category_id=3,
            size="M",
            condition="new",
            min_price=Decimal("10.00"),
            max_price=Decimal("99.99"),
            search="denim",
        )
        assert f.page == 2
        assert f.per_page == 24
        assert f.lang == "sv"
        assert f.category == 3
        assert f.size == "M"
        assert f.condition == "new"
        assert f.min_price == Decimal("10.00")
        assert f.max_price == Decimal("99.99")
        assert f.q == "denim"

    def test_page_must_be_positive(self):
        """page < 1 is rejected."""
        with pytest.raises(ValidationError):
            self.ProductFilter(page=0)

    def test_per_page_max_100(self):
        """per_page > 100 is rejected."""
        with pytest.raises(ValidationError):
            self.ProductFilter(per_page=200)

    def test_per_page_min_1(self):
        """per_page < 1 is rejected."""
        with pytest.raises(ValidationError):
            self.ProductFilter(per_page=0)

    def test_alias_search_maps_to_q(self):
        """The 'search' alias populates the 'q' field."""
        f = self.ProductFilter(search="jeans")
        assert f.q == "jeans"

    def test_alias_category_id_maps_to_category(self):
        """The 'category_id' alias populates the 'category' field."""
        f = self.ProductFilter(category_id=5)
        assert f.category == 5

    def test_lang_default_es(self):
        """lang defaults to Spanish when omitted."""
        f = self.ProductFilter()
        assert f.lang == "es"


class TestCreateProductRequest:
    """Validation of admin product creation payload."""

    @pytest.fixture(autouse=True)
    def _schema(self):
        from app.schemas.product import CreateProductRequest

        self.Schema = CreateProductRequest

    def test_valid_with_es_translation(self):
        """Minimum valid request: price + at least one translation."""
        data = {
            "translations": [
                {"language_code": "es", "name": "Chaqueta", "description": "Una chaqueta"}
            ],
            "price": Decimal("29.99"),
        }
        req = self.Schema(**data)
        assert req.price == Decimal("29.99")
        assert len(req.translations) == 1
        assert req.translations[0].lang == "es"

    def test_translations_list_must_not_be_empty(self):
        """At least one translation is required."""
        with pytest.raises(ValidationError):
            self.Schema(
                translations=[],
                price=Decimal("10.00"),
            )

    def test_price_must_be_positive(self):
        """Price <= 0 is rejected."""
        with pytest.raises(ValidationError):
            self.Schema(
                translations=[
                    {"language_code": "es", "name": "Test"}
                ],
                price=Decimal("0"),
            )

    def test_optional_fields_default_none(self):
        """category_id, size, brand, condition default to None."""
        req = self.Schema(
            translations=[
                {"language_code": "es", "name": "Test"}
            ],
            price=Decimal("15.00"),
        )
        assert req.category_id is None
        assert req.size is None
        assert req.brand is None
        assert req.condition is None

    def test_all_fields_set(self):
        """Full creation payload with all optional fields."""
        req = self.Schema(
            translations=[
                {"language_code": "es", "name": "Pantalón", "description": "Vaqueros"},
                {"language_code": "en", "name": "Trousers"},
            ],
            price=Decimal("49.99"),
            category_id=2,
            size="M",
            brand="Levi's",
            condition="like_new",
        )
        assert req.brand == "Levi's"
        assert req.size == "M"
        assert req.condition == "like_new"
        assert len(req.translations) == 2


class TestUpdateProductRequest:
    """Validation of admin product update payload (all fields optional)."""

    @pytest.fixture(autouse=True)
    def _schema(self):
        from app.schemas.product import UpdateProductRequest

        self.Schema = UpdateProductRequest

    def test_empty_body_allowed(self):
        """All fields are optional — empty body is valid."""
        req = self.Schema()
        assert req.price is None
        assert req.translations is None
        assert req.size is None

    def test_partial_price_update(self):
        """Only price can be updated."""
        req = self.Schema(price=Decimal("39.99"))
        assert req.price == Decimal("39.99")
        assert req.translations is None

    def test_stock_cannot_be_negative(self):
        """stock must be >= 0."""
        with pytest.raises(ValidationError):
            self.Schema(stock=-1)


class TestPaginationMeta:
    """Validation of pagination metadata schema."""

    @pytest.fixture(autouse=True)
    def _schema(self):
        from app.schemas.common import PaginationMeta

        self.Schema = PaginationMeta

    def test_pages_alias(self):
        """The 'pages' field name maps to 'total_pages'."""
        meta = self.Schema(page=1, per_page=12, total=25, pages=3)
        assert meta.total_pages == 3
        assert meta.page == 1
        assert meta.total == 25


class TestProductTranslationResponse:
    """Validation of translation response alias mapping."""

    def test_language_code_alias(self):
        from app.schemas.product import ProductTranslationResponse

        t = ProductTranslationResponse(language_code="es", name="Camisa")
        assert t.lang == "es"
        assert t.name == "Camisa"
