"""Unit tests for SKU generation helpers in VariantService.

Pure logic tests — no PostgreSQL needed. Tests color abbreviation,
slug prefix, and SKU collision resolution with minimal async mocks.
"""

from unittest.mock import AsyncMock

import pytest

from app.services.variant_service import VariantService


# ---------------------------------------------------------------------------
# Color abbreviation — static helper
# ---------------------------------------------------------------------------


class TestColorAbbreviation:
    def test_color_abbreviation(self):
        """_color_abbr returns 2-char uppercase abbreviation."""
        assert VariantService._color_abbr("Black") == "BL"
        assert VariantService._color_abbr("Red") == "RE"
        assert VariantService._color_abbr("Azul") == "AZ"

    def test_color_abbreviation_multi_word(self):
        """Multi-word colors take first letter of each word."""
        assert VariantService._color_abbr("Light Blue") == "LB"

    def test_color_abbreviation_none(self):
        """None or empty color returns None (_generate_variant_sku replaces with 'NC')."""
        assert VariantService._color_abbr(None) is None
        assert VariantService._color_abbr("") is None


# ---------------------------------------------------------------------------
# Slug prefix — static helper
# ---------------------------------------------------------------------------


class TestSkuSlugPrefix:
    def test_sku_slug_prefix(self):
        """_sku_slug_prefix returns uppercase prefix from slug."""
        assert VariantService._sku_slug_prefix("hoodie") == "HOOD"
        assert VariantService._sku_slug_prefix("ab") == "AB"
        # Multi-word slug: takes first letter of up to 3 parts
        assert VariantService._sku_slug_prefix("denim-jacket") == "DJ"


# ---------------------------------------------------------------------------
# SKU generation — async helper (light mocks)
# ---------------------------------------------------------------------------


class TestSkuGeneration:
    @pytest.mark.asyncio
    async def test_generate_variant_sku_basic(self):
        """_generate_variant_sku returns expected format."""
        svc = VariantService()
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)

        sku = await svc._generate_variant_sku(db, "hoodie", "M", "BL")
        assert sku == "HOOD-M-BL-01"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_no_size(self):
        """Null size uses 'NS' (No Size)."""
        svc = VariantService()
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)

        sku = await svc._generate_variant_sku(db, "hoodie", None, "RE")
        assert sku == "HOOD-NS-RE-01"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_no_color(self):
        """Null color uses 'NC' (No Color)."""
        svc = VariantService()
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)

        sku = await svc._generate_variant_sku(db, "hoodie", "M", None)
        assert sku == "HOOD-M-NC-01"

    @pytest.mark.asyncio
    async def test_generate_variant_sku_collision_increments_seq(self):
        """When SKU exists, seq increments until a free one is found."""
        svc = VariantService()
        db = AsyncMock()
        db.scalar = AsyncMock(side_effect=[True, True, None])

        sku = await svc._generate_variant_sku(db, "hoodie", "M", "BL")
        assert sku == "HOOD-M-BL-03"
