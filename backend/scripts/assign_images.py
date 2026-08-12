#!/usr/bin/env python3
"""Assign existing product images to seeded products (demo helper).

The real-data seed creates products without images (dataset shard has no
bytes column). This script copies pre-existing WebP images from the
uploads/products directory onto products that lack image_urls.
"""

import asyncio
import logging
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.engine import async_session
from app.models.product import Product

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("assign_images")

UPLOADS = Path(os.environ.get("UPLOAD_DIR", "./uploads")) / "products"


async def assign_images() -> None:
    images = sorted(p.name for p in UPLOADS.glob("*.webp")) if UPLOADS.is_dir() else []
    if not images:
        logger.error("No images found in %s", UPLOADS)
        return

    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        logger.info("📦 %d products, %d images disponibles", len(products), len(images))

        random.shuffle(images)
        assigned = 0
        for i, product in enumerate(products):
            if product.image_urls and len(product.image_urls) > 0:
                continue  # ya tiene imagen
            img = images[i % len(images)]
            product.image_urls = [f"/uploads/products/{img}"]
            assigned += 1
            if assigned % 50 == 0:
                await session.commit()
                logger.info("  …%d asignadas", assigned)

        await session.commit()
        logger.info("✅ %d productos con imagen asignada", assigned)


if __name__ == "__main__":
    asyncio.run(assign_images())
