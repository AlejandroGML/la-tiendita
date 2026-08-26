#!/usr/bin/env python3
"""Fetch REAL product images from the HF dataset, matched BY GARMENT TYPE.

The parquet shard has an empty 'bytes' column, but the HF rows API exposes
the 'image' field as {src: url}. This script:

1. Reads the parquet locally and groups rows by `type` (Blouse, T-shirt, …)
2. Fetches image.src URLs for those rows via the rows API
3. For each product in the DB, maps its category slug → dataset type and
   assigns an image of the SAME garment type (deterministic, coherent).
"""

import asyncio
import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import pyarrow.parquet as pq
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.engine import async_session
from app.models.product import Product

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fetch_real_images")

DATASET = "fnauman/fashion-second-hand-front-only-rgb"
ROWS_API = f"https://datasets-server.huggingface.co/rows?dataset={DATASET}&config=default&split=train"

# Mapeo categoría (slug BD) → type del dataset
CATEGORY_TO_TYPE = {
    "shirt": "Shirt", "t-shirt": "T-shirt", "sweater": "Sweater",
    "top": "Top", "dress": "Dress", "blouse": "Blouse",
    "cardigan": "Cardigan", "tank-top": "Tank Top", "jacker": "Jacket",
    "blazer": "Blazer", "nightgown": "Nightgown", "tunic": "Tunic",
    "pants": "Pants", "jeans": "Jeans", "skirt": "Skirt", "shorts": "Shorts",
    "shoes": "Shoes", "sneakers": "Sneakers", "boots": "Boots", "sandals": "Sandals",
    "hat": "Hat", "bag": "Bag", "scarf": "Scarf", "belt": "Belt",
    "coat": "Coat", "jacket": "Jacket", "vest": "Vest", "poncho": "Poncho",
}


def _shard_path() -> Path:
    return Path("/tmp/tiendita-ds/train-00000-of-00013.parquet")


async def fetch_image_urls_by_type(types_needed: set[str]) -> dict[str, list[str]]:
    """Fetch image.src URLs from the rows API, grouped by row type.

    The rows API serves ALL shards of the dataset (13 parquet files) with
    their REAL image URLs and their OWN type label — this is the source of
    truth. The local parquet shard is NOT used for ordering because the
    rows API order doesn't match it.
    """
    by_type: dict[str, list[str]] = defaultdict(list)
    async with httpx.AsyncClient(timeout=60) as client:
        offset = 0
        while True:
            resp = await client.get(f"{ROWS_API}&offset={offset}&length=100")
            resp.raise_for_status()
            rows = resp.json().get("rows", [])
            if not rows:
                break
            for r in rows:
                row = r.get("row", {})
                t = str(row.get("type") or "").strip()
                img = row.get("image")
                if t in types_needed and isinstance(img, dict) and img.get("src"):
                    by_type[t].append(img["src"])
            offset += len(rows)
            if offset >= 3000:  # suficiente para 25-50 productos
                break
            if offset % 500 == 0:
                logger.info("  …%d filas escaneadas", offset)
    return by_type


async def main(limit: int = 25) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.created_at)
            .limit(limit)
        )
        products = result.scalars().all()
        logger.info("🎯 %d productos en BD", len(products))

        # ¿Qué types necesitamos?
        types_needed = {
            CATEGORY_TO_TYPE.get(p.category.slug, "")
            for p in products
            if p.category is not None
        }
        types_needed.discard("")
        logger.info("Types requeridos: %s", sorted(types_needed))

        logger.info("⬇️  Obteniendo URLs por type (rows API)")
        urls_by_type = await fetch_image_urls_by_type(types_needed)
        for t, urls in urls_by_type.items():
            logger.info("  %s: %d imágenes", t, len(urls))

        upload_dir = Path(settings.UPLOAD_DIR) / "products"
        upload_dir.mkdir(parents=True, exist_ok=True)

        counters: dict[str, int] = defaultdict(int)
        assigned = 0
        async with httpx.AsyncClient(timeout=60) as client:
            for product in products:
                ds_type = CATEGORY_TO_TYPE.get(product.category.slug, "") if product.category else ""
                pool = urls_by_type.get(ds_type, [])
                idx = counters[ds_type]
                if not pool or idx >= len(pool):
                    logger.warning("  ⚠️ sin imagen para %s (type=%s)", product.slug, ds_type)
                    continue
                url = pool[idx]
                counters[ds_type] += 1
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    fname = f"{product.id.hex}.webp"
                    (upload_dir / fname).write_bytes(resp.content)
                    product.image_urls = [f"/uploads/products/{fname}"]
                    assigned += 1
                except Exception as exc:
                    logger.warning("  ⚠️ fallo %s: %s", product.slug, str(exc)[:60])
                if assigned % 10 == 0:
                    await session.commit()
                    logger.info("  …%d asignadas", assigned)
        await session.commit()
        logger.info("✅ %d productos con imagen REAL por tipo", assigned)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    asyncio.run(main(limit))
