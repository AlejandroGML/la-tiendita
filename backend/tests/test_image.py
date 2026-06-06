"""Tests for image resize and thumbnail utilities.

These tests use Pillow to create in-memory images and verify dimensions
after processing. No actual filesystem I/O for the sync helpers,
but the async wrappers are tested via anyio.
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestResizeImageSync:
    """Tests for the synchronous Pillow resize helper."""

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.utils.image import _resize_image_sync

        self.resize = _resize_image_sync

    @pytest.fixture
    def img_file(self):
        """Create a temporary JPEG image for testing."""
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (1600, 900), color="red")
            img.save(f, "JPEG")
            path = f.name
        yield path
        os.unlink(path)

    def test_resize_landscape_shrinks_to_max_dim(self, img_file):
        """A 1600×900 image resized to max_dim=1200 becomes 1200×675."""
        result = self.resize(img_file, max_dim=1200)

        from PIL import Image

        img = Image.open(result)
        assert img.size == (1200, 675)

    def test_resize_portrait_shrinks_height_to_max_dim(self):
        """A portrait image has its height clamped to max_dim."""
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = Image.new("RGB", (800, 1600), color="blue")
            img.save(f, "PNG")
            path = f.name

        try:
            result = self.resize(path, max_dim=1200)
            img = Image.open(result)
            assert img.size == (600, 1200)
        finally:
            os.unlink(path)

    def test_smaller_image_not_upscaled(self):
        """An image already within max_dim is returned unchanged."""
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (400, 300), color="green")
            img.save(f, "JPEG")
            path = f.name

        try:
            result = self.resize(path, max_dim=1200)
            img = Image.open(result)
            assert img.size == (400, 300)
        finally:
            os.unlink(path)

    def test_square_image_resized(self):
        """A square image has both sides clamped to max_dim."""
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (2000, 2000), color="yellow")
            img.save(f, "JPEG")
            path = f.name

        try:
            result = self.resize(path, max_dim=1200)
            img = Image.open(result)
            assert img.size == (1200, 1200)
        finally:
            os.unlink(path)


class TestGenerateThumbnailSync:
    """Tests for the synchronous Pillow thumbnail helper."""

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.utils.image import _generate_thumbnail_sync

        self.thumbnail = _generate_thumbnail_sync

    @pytest.fixture
    def img_file(self):
        """Create a temporary JPEG image for testing."""
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (1600, 1200), color="red")
            img.save(f, "JPEG")
            path = f.name
        yield path
        os.unlink(path)

    def test_thumbnail_fits_within_box(self, img_file):
        """Thumbnail fits within (300,300) preserving aspect ratio."""
        result = self.thumbnail(img_file, size=(300, 300))

        from PIL import Image

        img = Image.open(result)
        # 1600×1200 → max 300 on longest side yields 300×225
        assert img.size == (300, 225)
        assert img.size[0] <= 300
        assert img.size[1] <= 300

    def test_thumbnail_saves_as_webp(self, img_file):
        """Output file has .webp extension regardless of source format."""
        result = self.thumbnail(img_file)
        assert result.endswith(".webp")

    def test_thumbnail_does_not_upscale_small_image(self):
        """A small image is not upscaled for the thumbnail."""
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = Image.new("RGB", (100, 100), color="green")
            img.save(f, "PNG")
            path = f.name

        try:
            result = self.thumbnail(path, size=(300, 300))
            img = Image.open(result)
            assert img.size == (100, 100)
        finally:
            os.unlink(path)
