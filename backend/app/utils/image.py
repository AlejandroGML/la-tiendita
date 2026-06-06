"""Image processing utilities using Pillow with thread-safe async wrappers.

All I/O-bound Pillow operations are dispatched via
``anyio.to_thread.run_sync`` to avoid blocking the async event loop.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from anyio import to_thread

from app.config import settings


def _resize_image_sync(file_path: str, max_dim: int = 1200) -> str:
    """Resize an image so its longest side ≤ *max_dim*, keeping aspect ratio.

    Returns the file path of the resized version. If the image is already
    smaller than *max_dim* on both axes, it is returned unchanged (no
    upscaling).  The original file is overwritten with the resized version.
    """
    from PIL import Image

    img = Image.open(file_path)
    original = img.size
    width, height = original

    if width <= max_dim and height <= max_dim:
        return file_path  # No resize needed — image already fits

    if width >= height:
        new_width = max_dim
        new_height = int(height * (max_dim / width))
    else:
        new_height = max_dim
        new_width = int(width * (max_dim / height))

    img = img.resize((new_width, new_height), Image.LANCZOS)
    img.save(file_path)
    return file_path


def _generate_thumbnail_sync(
    file_path: str, size: tuple[int, int] = (300, 300)
) -> str:
    """Generate a thumbnail for the given image file.

    Returns the file path of the thumbnail (``{stem}_thumb{ext}``).
    The thumbnail fits inside *size* preserving aspect ratio.
    """
    from PIL import Image

    img = Image.open(file_path)
    img.thumbnail(size, Image.LANCZOS)

    path = Path(file_path)
    thumb_path = path.with_stem(f"{path.stem}_thumb")
    thumb_path = thumb_path.with_suffix(".webp")
    img.save(str(thumb_path), "WEBP", quality=85)
    return str(thumb_path)


# ---------------------------------------------------------------------------
# Async wrappers
# ---------------------------------------------------------------------------


async def resize_image(
    file_path: str, max_dim: Optional[int] = None
) -> str:
    """Async wrapper around Pillow resize — dispatched to a thread."""
    if max_dim is None:
        max_dim = settings.MAX_IMAGE_DIMENSION
    return await to_thread.run_sync(_resize_image_sync, file_path, max_dim)


async def generate_thumbnail(
    file_path: str, size: tuple[int, int] = (300, 300)
) -> str:
    """Async wrapper around Pillow thumbnail generation — dispatched to a thread."""
    return await to_thread.run_sync(_generate_thumbnail_sync, file_path, size)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ensure_upload_dir() -> None:
    """Create the upload directory if it does not exist."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
