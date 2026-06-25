"""UploadController — admin-only image upload with Pillow processing.

POST /api/upload (multipart) — validates MIME, resizes, generates thumbnail,
and returns public URLs.
"""

import os
import uuid
from pathlib import Path

from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ValidationException
from litestar.params import Body

from app.config import settings
from app.core.arq import get_arq_redis
from app.guards.admin_guard import admin_guard
from app.utils.image import ensure_upload_dir

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class UploadController(Controller):
    """Admin-only image upload — JWT + admin role required."""

    path = "/api"
    tags = ["upload"]
    guards = [admin_guard]

    @post(
        "/upload",
        status_code=201,
    )
    async def upload_image(
        self,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    ) -> dict:
        """Upload an image file, resize, generate thumbnail, and return
        public URLs.

        Accepted MIME types: ``image/jpeg``, ``image/png``, ``image/webp``.
        Max file size: 5 MB (configurable via ``MAX_IMAGE_SIZE``).
        """
        # --- Validate MIME --------------------------------------------------
        content_type = data.content_type
        if content_type not in ALLOWED_MIME_TYPES:
            raise ValidationException(
                detail="unsupported file type: must be JPEG, PNG, or WebP"
            )

        # --- Read file content ----------------------------------------------
        file_bytes = await data.read()

        # --- Validate size --------------------------------------------------
        if len(file_bytes) > settings.MAX_IMAGE_SIZE:
            raise ValidationException(
                detail=f"file exceeds maximum size of {settings.MAX_IMAGE_SIZE // (1024 * 1024)} MB"
            )

        # --- Save to disk ---------------------------------------------------
        ensure_upload_dir()
        ext = EXTENSION_MAP.get(content_type, ".jpg")
        file_id = uuid.uuid4().hex
        filename = f"{file_id}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # --- Enqueue background job for resize + thumbnail ------------------
        redis = await get_arq_redis()
        await redis.enqueue_job("process_image", file_path)

        # Predict thumbnail path — identical to _generate_thumbnail_sync logic.
        thumb_path = str(
            Path(file_path).with_stem(f"{Path(file_path).stem}_thumb").with_suffix(".webp")
        )

        # --- Build URLs -----------------------------------------------------
        image_url = f"/uploads/{os.path.basename(file_path)}"
        thumbnail_url = f"/uploads/{os.path.basename(thumb_path)}"

        return {
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
        }
