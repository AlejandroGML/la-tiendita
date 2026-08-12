#!/usr/bin/env python3
"""Add size/color variants with stock to seeded products.

The real-data seed (seed_real.py) creates products WITHOUT variants, so
stock_total = 0 and nothing can be purchased. This script gives every
product 2-3 variants (random sizes, stock 3-12) so the checkout flow
works end-to-end in the demo.
"""

import asyncio
import logging
import random
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.engine import async_session
from app.models.product import Product, ProductSize
from app.models.product_variant import ProductVariant

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("add_variants")

SIZES = [ProductSize.XS, ProductSize.S, ProductSize.M, ProductSize.L, ProductSize.XL]
COLORS = ["Negro", "Blanco", "Azul", "Gris", "Beige", "Verde"]


async def add_variants() -> None:
    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        logger.info("📦 %d products sin variantes", len(products))

        total = 0
        for product in products:
            # Skip products that already have variants
            existing = await session.execute(
                select(ProductVariant).where(ProductVariant.product_id == product.id)
            )
            if existing.scalars().first() is not None:
                continue

            n_variants = random.randint(2, 3)
            used_sizes: set[ProductSize] = set()
            for _ in range(n_variants):
                size = random.choice(SIZES)
                while size in used_sizes:
                    size = random.choice(SIZES)
                used_sizes.add(size)

                variant = ProductVariant(
                    product_id=product.id,
                    size=size,
                    color=random.choice(COLORS),
                    stock=random.randint(3, 12),
                    reserved_stock=0,
                    sku=f"{product.id.hex[:8]}-{size.value}-{uuid.uuid4().hex[:4]}",
                )
                session.add(variant)
                total += 1

            if total % 50 == 0:
                await session.commit()
                logger.info("  …%d variantes", total)

        await session.commit()
        logger.info("✅ %d variantes creadas para %d productos", total, len(products))


if __name__ == "__main__":
    asyncio.run(add_variants())
