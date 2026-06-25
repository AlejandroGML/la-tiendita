"""Serializer snapshot tests (no DB required).

Verifies the builders extracted into ``app.serializers`` produce the
documented response shape. Uses lightweight attribute fakes rather than ORM
instances so the tests run without a database — they lock the serialization
contract that both controllers and the cache-aside path depend on.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.serializers.category import (
    build_category_list_item,
    build_category_response,
)
from app.serializers.product import build_product_response


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _translation(code, name, description=""):
    return SimpleNamespace(language_code=code, name=name, description=description)


def _variant(vid, pid, size=None, color=None, deleted=False, stock=5, sku="SKU1"):
    return SimpleNamespace(
        id=vid,
        product_id=pid,
        size=SimpleNamespace(value=size) if size else None,
        color=color,
        color_hex="#abc",
        stock=stock,
        sku=sku,
        deleted_at=datetime(2020, 1, 1, tzinfo=timezone.utc) if deleted else None,
    )


def _make_product(**overrides):
    pid = uuid4()
    defaults = dict(
        id=pid,
        slug="chaqueta-denim",
        price=Decimal("19.99"),
        category_id=3,
        brand="Levi",
        condition=SimpleNamespace(value="new"),
        condition_rating=5,
        condition_details="like new",
        target_gender="unisex",
        material="denim",
        colors=["Blue"],
        trend="casual",
        pattern="solid",
        season="all",
        cut="regular",
        usage="daily",
        source_dataset="seed",
        image_urls=["/img/1.png"],
        translations=[
            _translation("es", "Chaqueta Denim", "Descripcion ES"),
            _translation("en", "Denim Jacket", "Description EN"),
        ],
        variants=[_variant(uuid4(), pid, size="M")],
        created_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Product serializer
# ---------------------------------------------------------------------------


def test_build_product_response_full_shape():
    product = _make_product()

    result = build_product_response(product)

    assert result["id"] == str(product.id)
    assert result["slug"] == "chaqueta-denim"
    assert result["price"] == "19.99"
    assert result["condition"] == "new"
    assert result["variant_count"] == 1
    assert result["variants"][0]["size"] == "M"
    assert result["sale_price"] is None
    assert result["promotion"] is None
    assert len(result["translations"]) == 2


def test_build_product_response_lang_filter_with_fallback():
    product = _make_product()

    result = build_product_response(product, lang="es")

    # Only the ES translation remains when lang is requested.
    assert [t["language_code"] for t in result["translations"]] == ["es"]
    assert result["translations"][0]["name"] == "Chaqueta Denim"


def test_build_product_response_lang_missing_falls_back_to_en():
    product = _make_product()

    result = build_product_response(product, lang="sv")

    # SV absent -> falls back to EN.
    assert [t["language_code"] for t in result["translations"]] == ["en"]


def test_build_product_response_attaches_promotion_info():
    product = _make_product()
    promo = SimpleNamespace(
        code="SUMMER10",
        discount_percent=10,
        end_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
    )
    promotion_info = {product.id: {"promotion": promo, "sale_price": 17.99}}

    result = build_product_response(product, promotion_info=promotion_info)

    assert result["sale_price"] == "17.99"
    assert result["promotion"]["code"] == "SUMMER10"
    assert result["promotion"]["discount_percent"] == 10


def test_build_product_response_excludes_deleted_variants():
    pid = uuid4()
    product = _make_product(
        id=pid,
        variants=[
            _variant(uuid4(), pid, size="M"),
            _variant(uuid4(), pid, size="L", deleted=True),
        ],
    )

    result = build_product_response(product)

    assert result["variant_count"] == 1
    assert [v["size"] for v in result["variants"]] == ["M"]


# ---------------------------------------------------------------------------
# Category serializer
# ---------------------------------------------------------------------------


def _make_category(translations):
    return SimpleNamespace(
        id=7,
        slug="zapatos",
        image_url="/img/zapatos.png",
        translations=translations,
    )


def test_build_category_response_full_translations():
    category = _make_category([_translation("es", "Zapatos"), _translation("en", "Shoes")])

    result = build_category_response(category)

    assert result["id"] == 7
    assert result["slug"] == "zapatos"
    assert result["image_url"] == "/img/zapatos.png"
    assert [t["language_code"] for t in result["translations"]] == ["es", "en"]


def test_build_category_list_item_requested_lang():
    category = _make_category([_translation("es", "Zapatos"), _translation("en", "Shoes")])

    result = build_category_list_item(category, "es")

    assert result == {"id": 7, "slug": "zapatos", "name": "Zapatos"}


def test_build_category_list_item_falls_back_to_en():
    category = _make_category([_translation("es", "Zapatos"), _translation("en", "Shoes")])

    result = build_category_list_item(category, "sv")

    assert result["name"] == "Shoes"


def test_build_category_list_item_falls_back_to_first():
    category = _make_category([_translation("fr", "Chaussures")])

    result = build_category_list_item(category, "sv")

    assert result["name"] == "Chaussures"
