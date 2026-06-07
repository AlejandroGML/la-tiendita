"""Tests for slug generation and collision resolution."""

import pytest


class TestSlugify:
    """Unit tests for ProductService.slugify static method."""

    @pytest.fixture(autouse=True)
    def _service(self):
        from app.services.product_service import ProductService

        self.service = ProductService()

    def test_basic_spanish_name(self):
        """Lowercases and hyphenates a simple Spanish name."""
        result = self.service.slugify("Chaqueta Denim")
        assert result == "chaqueta-denim"

    def test_strips_accents(self):
        """NFKD normalisation removes Spanish accents."""
        result = self.service.slugify("cañón")
        assert result == "canon"

    def test_removes_special_chars(self):
        """Punctuation and special characters become hyphens or are removed."""
        result = self.service.slugify("Hello! World? #1")
        assert result == "hello-world-1"

    def test_multiple_spaces_and_dashes(self):
        """Runs of non-alphanumeric chars collapse to a single hyphen."""
        result = self.service.slugify("foo   ---   bar")
        assert result == "foo-bar"

    def test_trailing_hyphens_stripped(self):
        """Leading and trailing hyphens are removed."""
        result = self.service.slugify("  ---hello---  ")
        assert result == "hello"

    def test_swedish_characters(self):
        """NFKD handles Swedish åäö by dropping diacritics."""
        result = self.service.slugify("Tröja")
        assert result == "troja"

    def test_empty_string_fallback(self):
        """An empty or whitespace-only name falls back to 'producto'."""
        result = self.service.slugify("   ")
        assert result == "producto"

    def test_numbers_preserved(self):
        """Digits are preserved in the slug."""
        result = self.service.slugify("Model 3000")
        assert result == "model-3000"

    def test_emoji_only_fallback(self):
        """Emoji-only input falls back to 'producto'."""
        result = self.service.slugify("😀🎉💯")
        assert result == "producto"

    def test_special_chars_only_fallback(self):
        """Input composed entirely of special characters falls back to 'producto'."""
        result = self.service.slugify("!@#$%^&*()")
        assert result == "producto"

    def test_300_char_input_truncated(self):
        """A 300-char ASCII input produces slug ≤ 200 chars."""
        name = "a" * 300
        result = self.service.slugify(name)
        # slugify does NOT truncate — the 200-char limit is applied in
        # generate_slug().  Here we just verify slugify() handles long
        # input without crashing.
        assert len(result) == 300
        assert result == "a" * 300

    def test_chinese_characters(self):
        """Chinese characters are stripped (not transliterable to ascii)."""
        result = self.service.slugify("牛仔裤")
        assert result == "producto"


class TestGenerateSlugCollision:
    """Integration-style tests for slug collision resolution.

    These tests use a mock session to simulate database lookups.
    """

    @pytest.fixture
    def svc(self):
        from app.services.product_service import ProductService

        return ProductService()

    @pytest.fixture
    def mock_session(self):
        from unittest.mock import AsyncMock

        session = AsyncMock()
        return session

    @staticmethod
    def _make_result(return_value):
        """Build a mock execute result with scalar_one_or_none()."""
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = return_value
        return mock_result

    @pytest.mark.asyncio
    async def test_no_collision_returns_base(self, svc, mock_session):
        """When slug is unique, the base slug is returned unchanged."""
        mock_session.execute.return_value = self._make_result(None)

        slug = await svc.generate_slug(mock_session, "Chaqueta Denim")
        assert slug == "chaqueta-denim"

    @pytest.mark.asyncio
    async def test_collision_appends_2(self, svc, mock_session):
        """When base slug exists, suffix '-2' is appended."""
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            # First call: existing slug found, second: no collision
            val = "some-id" if call_count[0] == 1 else None
            return TestGenerateSlugCollision._make_result(val)

        mock_session.execute.side_effect = side_effect

        slug = await svc.generate_slug(mock_session, "Chaqueta Denim")
        assert slug == "chaqueta-denim-2"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_collision_appends_3_when_2_taken(self, svc, mock_session):
        """When base and -2 both exist, suffix '-3' is appended."""
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            val = "some-id" if call_count[0] <= 2 else None
            return TestGenerateSlugCollision._make_result(val)

        mock_session.execute.side_effect = side_effect

        slug = await svc.generate_slug(mock_session, "Chaqueta Denim")
        assert slug == "chaqueta-denim-3"
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_truncation_long_base(self, svc, mock_session):
        """A 500-char unicode name produces a truncated slug ≤ 200 chars."""
        name = "café " * 125  # ~500 chars, "café" → "cafe" after slugify
        mock_session.execute.return_value = self._make_result(None)

        slug = await svc.generate_slug(mock_session, name)
        assert len(slug) <= 200
        assert slug.startswith("cafe-cafe")

    @pytest.mark.asyncio
    async def test_truncation_boundary_at_200(self, svc, mock_session):
        """A slug exactly 200 chars is not truncated."""
        name = "a" * 200
        mock_session.execute.return_value = self._make_result(None)

        slug = await svc.generate_slug(mock_session, name)
        assert len(slug) == 200
        assert slug == "a" * 200

    @pytest.mark.asyncio
    async def test_truncation_with_collision(self, svc, mock_session):
        """Long name where truncated slug collides — suffix appended after truncation."""
        name = "x" * 300  # slugify produces 'x' * 300, truncated to 200
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            # First call: collision.  Second: no collision.
            val = "some-id" if call_count[0] == 1 else None
            return TestGenerateSlugCollision._make_result(val)

        mock_session.execute.side_effect = side_effect

        slug = await svc.generate_slug(mock_session, name)
        assert len(slug) <= 200
        assert slug.endswith("-2")
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_truncation_deep_collision(self, svc, mock_session):
        """Long name with deep collision — suffix '-999' still fits within 200."""
        name = "y" * 400  # slugify produces 'y' * 400, truncated to 200
        # Collide 998 times so attempt reaches 999 (suffix "-999" is 4 chars)
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            val = "some-id" if call_count[0] <= 998 else None
            return TestGenerateSlugCollision._make_result(val)

        mock_session.execute.side_effect = side_effect

        slug = await svc.generate_slug(mock_session, name)
        assert len(slug) <= 200
        assert slug.endswith("-999")
        assert call_count[0] == 999
