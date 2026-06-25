"""ARQ worker: image processing jobs.

Defines the ``process_image`` job and the ``WorkerSettings`` class
consumed by the ``arq`` CLI (``arq app.worker.jobs.WorkerSettings``).
"""

from arq.connections import RedisSettings

from app.config import settings
from app.utils.image import generate_thumbnail, resize_image


async def process_image(ctx: dict, file_path: str) -> dict:
    """Resize the uploaded image and generate a WebP thumbnail.

    Called by the ARQ worker.  Uses the existing ``resize_image`` and
    ``generate_thumbnail`` async helpers (which dispatch blocking Pillow
    work to a thread via ``anyio.to_thread.run_sync``).

    Args:
        ctx: ARQ context dict (contains ``job_id``, ``job_try``, and any
             keys set by ``on_startup``).
        file_path: Absolute or relative path to the uploaded image file.

    Returns:
        dict with ``image_url`` and ``thumbnail_url`` keys.
    """
    await resize_image(file_path)
    thumb_path = await generate_thumbnail(file_path)
    return {"image_url": file_path, "thumbnail_url": thumb_path}


class WorkerSettings:
    """ARQ worker configuration — consumed by the ``arq`` CLI."""

    functions = [process_image]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
