"""Tests for ARQ background image processing.

Covers:
- 4.1  Unit: ``process_image`` calls helpers with correct args.
- 4.2  Integration: upload controller enqueues job and returns fast.
- 4.3  Integration: worker processes job end-to-end with real files.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# 4.1  Unit — process_image calls helpers correctly
# ---------------------------------------------------------------------------

class TestProcessImageJob:
    """Verify the ARQ job invokes the image helpers with the right path."""

    @pytest.mark.asyncio
    async def test_process_image_calls_resize_and_thumbnail(self):
        """``process_image`` calls ``resize_image`` then ``generate_thumbnail``
        with the given file path and returns expected dict."""
        from app.worker.jobs import process_image

        file_path = "/tmp/test-image.jpg"
        ctx: dict = {}  # minimal ARQ context

        with (
            patch("app.worker.jobs.resize_image", new_callable=AsyncMock) as mock_resize,
            patch(
                "app.worker.jobs.generate_thumbnail",
                new_callable=AsyncMock,
                return_value="/tmp/test-image_thumb.webp",
            ) as mock_thumb,
        ):
            result = await process_image(ctx, file_path)

        mock_resize.assert_awaited_once_with(file_path)
        mock_thumb.assert_awaited_once_with(file_path)
        assert result == {
            "image_url": file_path,
            "thumbnail_url": "/tmp/test-image_thumb.webp",
        }

    @pytest.mark.asyncio
    async def test_process_image_with_different_paths(self):
        """The job passes the exact file path through to both helpers."""
        from app.worker.jobs import process_image

        ctx: dict = {}
        paths = [
            "/app/uploads/abc123.jpg",
            "./uploads/def456.png",
            "ghi789.webp",
        ]

        for fp in paths:
            with (
                patch("app.worker.jobs.resize_image", new_callable=AsyncMock) as mock_resize,
                patch(
                    "app.worker.jobs.generate_thumbnail",
                    new_callable=AsyncMock,
                    return_value=f"{fp}_thumb.webp",
                ) as mock_thumb,
            ):
                await process_image(ctx, fp)

            mock_resize.assert_awaited_once_with(fp)
            mock_thumb.assert_awaited_once_with(fp)


# ---------------------------------------------------------------------------
# 4.2  Integration — upload enqueues job
# ---------------------------------------------------------------------------

class TestUploadEnqueuesJob:
    """The upload controller delegates processing to ARQ instead of calling
    Pillow helpers directly."""

    @pytest.mark.asyncio
    async def test_upload_enqueues_arq_job_and_returns_urls(self):
        """The upload method saves the file, enqueues ``"process_image"``
        via ARQ, and returns predictable ``image_url``/``thumbnail_url``
        without calling Pillow helpers directly."""
        import io
        import tempfile
        from unittest.mock import MagicMock

        from litestar.datastructures import UploadFile

        from app.controllers.upload import UploadController

        # Litestar Controllers require an owner; use a mock.
        controller = UploadController(owner=MagicMock())

        # Build a minimal JPEG file as raw bytes for UploadFile.
        img_bytes = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01"
            b"\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07"
            b"\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b"
            b"\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a"
            b"\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01"
            b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04"
            b"\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02"
            b"\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}"
            b"\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\""
            b"\x71\x14\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br"
            b"\x82\x09\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJS"
            b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00"
            b"\xfb\xd2\x94\xa0\x0f\xff\xd9"
        )

        data = UploadFile(
            content_type="image/jpeg",
            filename="test.jpg",
            file_data=img_bytes,
        )

        mock_redis = AsyncMock()
        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "app.controllers.upload.settings"
        ) as mock_settings, patch(
            "app.controllers.upload.get_arq_redis",
            return_value=mock_redis,
        ):
            mock_settings.UPLOAD_DIR = tmpdir
            mock_settings.MAX_IMAGE_SIZE = 5 * 1024 * 1024

            # Call the raw async method via the handler's ``fn`` attribute
            # (bypasses Litestar route handler __call__ wrapper).
            response = await UploadController.upload_image.fn(
                controller, data=data
            )

            # Response contract: both URLs returned immediately.
            assert response["image_url"].startswith("/uploads/")
            assert response["thumbnail_url"].startswith("/uploads/")
            assert response["thumbnail_url"].endswith("_thumb.webp")

            # Verify ARQ enqueue was called.
            mock_redis.enqueue_job.assert_awaited_once()
            call_args = mock_redis.enqueue_job.call_args
            assert call_args[0][0] == "process_image"
            # File path should match the image_url filename.
            assert os.path.basename(call_args[0][1]).startswith(
                os.path.basename(response["image_url"]).split(".")[0]
            )


# ---------------------------------------------------------------------------
# 4.3  Integration — worker processes job end-to-end
# ---------------------------------------------------------------------------

class TestWorkerEndToEnd:
    """Full pipeline: save file → call ``process_image`` → verify files."""

    @pytest.mark.asyncio
    async def test_process_image_produces_correct_output_files(self):
        """After ``process_image`` runs, a resized original and a WebP
        thumbnail exist with expected dimensions."""
        from PIL import Image

        from app.worker.jobs import process_image

        ctx: dict = {}

        # Create a 1600×900 test image on disk.
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.jpg")
            img = Image.new("RGB", (1600, 900), color="red")
            img.save(file_path, "JPEG")

            # Override UPLOAD_DIR so helpers write to tmpdir.
            with patch("app.config.settings.UPLOAD_DIR", tmpdir), patch(
                "app.config.settings.MAX_IMAGE_DIMENSION", 1200
            ):
                result = await process_image(ctx, file_path)

            # Verify returned dict.
            assert result["image_url"] == file_path
            thumb_path = result["thumbnail_url"]
            assert thumb_path.endswith("_thumb.webp")

            # Verify files exist.
            assert os.path.isfile(file_path)
            assert os.path.isfile(thumb_path)

            # Verify dimensions.
            resized = Image.open(file_path)
            assert resized.size == (1200, 675)  # 1600×900 → max_dim=1200

            thumb = Image.open(thumb_path)
            # 1200×675 → thumbnail within (300,300) → 300×169
            assert thumb.size[0] <= 300
            assert thumb.size[1] <= 300
            assert thumb.format == "WEBP"

    @pytest.mark.asyncio
    async def test_small_image_not_upscaled(self):
        """An image smaller than max_dim is left unchanged."""
        from PIL import Image

        from app.worker.jobs import process_image

        ctx: dict = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "small.png")
            img = Image.new("RGB", (200, 150), color="blue")
            img.save(file_path, "PNG")

            with patch("app.config.settings.UPLOAD_DIR", tmpdir), patch(
                "app.config.settings.MAX_IMAGE_DIMENSION", 1200
            ):
                result = await process_image(ctx, file_path)

            resized = Image.open(file_path)
            assert resized.size == (200, 150)

            thumb = Image.open(result["thumbnail_url"])
            assert thumb.size == (200, 150)
            assert thumb.format == "WEBP"

    @pytest.mark.asyncio
    async def test_concurrent_jobs_produce_correct_files(self):
        """Three concurrent ``process_image`` calls each produce correct
        output without corruption."""
        import asyncio

        from PIL import Image

        from app.worker.jobs import process_image

        ctx: dict = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create three images of different sizes.
            specs = [
                ("img1.jpg", (1600, 900), "red"),
                ("img2.jpg", (800, 1600), "green"),
                ("img3.png", (2000, 2000), "blue"),
            ]

            paths = []
            for name, size, color in specs:
                fp = os.path.join(tmpdir, name)
                img = Image.new("RGB", size, color=color)
                img.save(fp, "JPEG" if name.endswith(".jpg") else "PNG")
                paths.append(fp)

            with patch("app.config.settings.UPLOAD_DIR", tmpdir), patch(
                "app.config.settings.MAX_IMAGE_DIMENSION", 1200
            ):
                results = await asyncio.gather(
                    *(process_image(ctx, fp) for fp in paths)
                )

            # Verify each result.
            for result, (name, size, _) in zip(results, specs):
                assert result["image_url"].endswith(name)
                assert result["thumbnail_url"].endswith("_thumb.webp")
                assert os.path.isfile(result["image_url"])
                assert os.path.isfile(result["thumbnail_url"])
