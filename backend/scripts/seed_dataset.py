#!/usr/bin/env python3
"""Seed TiendaVirtual database with the HuggingFace fashion-second-hand dataset.

Usage::

    cd backend
    uv run python scripts/seed_dataset.py [--limit N] [--batch-size 100]

The script downloads ``fnauman/fashion-second-hand-front-only-rgb`` via the
``datasets`` library, maps every field to the Product model, creates categories
on-the-fly, and inserts in configurable batch sizes.

Requires a running PostgreSQL database pointed to by ``DATABASE_URL``.
"""

import argparse
import ast
import asyncio
import logging
import sys
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from PIL import Image as PILImage

from app.db.engine import async_session
from app.models.category import Category, CategoryTranslation
from app.models.product import Product, ProductCondition, ProductTranslation
from app.services.slug_service import SlugService

logger = logging.getLogger("seed_dataset")

# ---------------------------------------------------------------------------
# Price range → Decimal midpoint
# ---------------------------------------------------------------------------
PRICE_RANGE_MAP: dict[str, Decimal] = {
    "<50": Decimal("25.00"),
    "50-100": Decimal("75.00"),
    "100-150": Decimal("125.00"),
    "150-200": Decimal("175.00"),
    "200-250": Decimal("225.00"),
    "250-300": Decimal("275.00"),
    ">300": Decimal("350.00"),
}


def parse_price(price_str: str | None) -> Decimal:
    """Convert a dataset price range to a Decimal midpoint."""
    if price_str is None:
        return Decimal("50.00")
    return PRICE_RANGE_MAP.get(price_str, Decimal("50.00"))


# ---------------------------------------------------------------------------
# Condition int → ProductCondition enum
# ---------------------------------------------------------------------------
CONDITION_MAP: dict[int, ProductCondition] = {
    1: ProductCondition.NEW,
    2: ProductCondition.LIKE_NEW,
    3: ProductCondition.GOOD,
    4: ProductCondition.FAIR,
    5: ProductCondition.FAIR,
}


def map_condition(condition_int: int | None) -> tuple[ProductCondition | None, int | None]:
    """Map dataset condition (1-5) to enum + rating."""
    if condition_int is None:
        return None, None
    rating = max(1, min(5, int(condition_int)))
    return CONDITION_MAP.get(rating), rating


# ---------------------------------------------------------------------------
# JSON-list string parsing
# ---------------------------------------------------------------------------
def parse_list(raw: str | None) -> list | None:
    """Parse a dataset list string like \"['Pink', 'Blue']\" to a Python list."""
    if raw is None or raw == "[]" or raw == "":
        return None
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed
    except (ValueError, SyntaxError):
        pass
    return None


# ---------------------------------------------------------------------------
# Condition details builder
# ---------------------------------------------------------------------------
def build_condition_details(
    pilling: int | None,
    damage: str | None,
    stains: str | None,
    holes: str | None,
    smell: str | None,
) -> dict | None:
    """Aggregate defect fields into a JSONB-ready dict."""
    details: dict = {}
    if pilling is not None:
        details["pilling"] = int(pilling)
    if damage and damage != "null":
        details["damage"] = damage
    if stains and stains not in ("No", "null"):
        details["stains"] = stains
    if holes and holes not in ("No", "null"):
        details["holes"] = holes
    if smell and smell != "null":
        details["smell"] = smell
    return details if details else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def create_categories(session: AsyncSession, types: set[str]) -> dict[str, int]:
    """Ensure a category exists for every unique *type* from the dataset.

    Returns a mapping of type_name → category_id.
    """
    # Load existing categories with eager-loaded translations
    result = await session.execute(
        select(Category).options(selectinload(Category.translations))
    )
    existing = {ct.name: cat for cat in result.scalars() for ct in cat.translations if ct.language_code == "en"}

    mapping: dict[str, int] = {}

    for type_name in sorted(types):
        if type_name in existing:
            mapping[type_name] = existing[type_name].id
            continue

        slug = SlugService.slugify(type_name)
        cat = Category(slug=slug)
        session.add(cat)
        await session.flush()

        # Translations: EN = type_name, ES = type_name (same for simplicity)
        session.add(CategoryTranslation(category_id=cat.id, language_code="en", name=type_name))
        session.add(CategoryTranslation(category_id=cat.id, language_code="es", name=type_name))
        await session.flush()

        mapping[type_name] = cat.id
        logger.info("Created category %s (id=%d)", type_name, cat.id)

    await session.commit()
    return mapping


async def seed(
    limit: int | None = None,
    batch_size: int = 100,
) -> None:
    """Download the dataset and insert rows into the products table."""
    from datasets import load_dataset

    logger.info("Loading dataset fnauman/fashion-second-hand-front-only-rgb (streaming) …")
    ds = load_dataset(
        "fnauman/fashion-second-hand-front-only-rgb",
        split="train",
        streaming=True,
    )

    # Ensure uploads directory exists
    uploads_dir = Path("/app/uploads/dataset")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Images will be saved to %s", uploads_dir)

    # Known types from the dataset (avoids full iteration for category creation)
    KNOWN_TYPES: set[str] = {
        "Top", "T-shirt", "Dress", "Sweater", "Shirt", "Blouse",
        "Blazer", "Tank Top", "Skirt", "Pants", "Jeans", "Jacket",
        "Coat", "Vest", "Shorts", "Jumpsuit", "Playsuit", "Cardigan",
        "Tunic", "Poncho", "Scarf", "Hat", "Belt", "Bag", "Shoes",
        "Boots", "Sandals", "Sneakers", "Heels", "Accessories",
    }
    all_types: set[str] = KNOWN_TYPES

    # Stream first N rows
    rows: list[dict] = []
    for i, row in enumerate(ds):
        rows.append(row)
        if limit and len(rows) >= limit:
            break

    total = len(rows)
    logger.info("Streamed %d rows", total)

    async with async_session() as session:
        # Phase 1 — create categories
        logger.info("Creating %d categories …", len(all_types))
        cat_map = await create_categories(session, all_types)
        await session.commit()

        # Phase 2 — insert products
        inserted = 0
        errors = 0

        for i, row in enumerate(rows):
            try:
                type_name = str(row.get("type") or "Unknown")
                brand = str(row.get("brand") or "Unknown Brand")[:100]
                category_id = cat_map.get(type_name)

                # Price
                price = parse_price(row.get("price"))

                # Condition
                condition_enum, condition_rating = map_condition(row.get("condition"))

                # Condition details
                condition_details = build_condition_details(
                    row.get("pilling"),
                    str(row.get("damage", "") or ""),
                    str(row.get("stains", "") or ""),
                    str(row.get("holes", "") or ""),
                    str(row.get("smell", "") or ""),
                )

                # Colors, cut
                colors = parse_list(str(row.get("colors", "")))
                cut = parse_list(str(row.get("cut", "")))

                # Text for translation
                text = str(row.get("text") or "").strip()

                # Material
                material = str(row.get("material") or "")[:255] or None

                # Slug: brand + type
                name_for_slug = f"{brand} {type_name}"
                slug = SlugService.slugify(name_for_slug)

                # Ensure slug uniqueness
                existing = await session.execute(
                    select(Product.id).where(Product.slug == slug)
                )
                if existing.scalar_one_or_none() is not None:
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                product = Product(
                    slug=slug,
                    price=price,
                    category_id=category_id,
                    brand=brand,
                    condition=condition_enum,
                    condition_rating=condition_rating,
                    condition_details=condition_details,
                    target_gender=str(row.get("category") or "")[:20] or None,
                    material=material,
                    colors=colors,
                    trend=str(row.get("trend") or "")[:50] or None,
                    pattern=str(row.get("pattern") or "")[:50] or None,
                    season=str(row.get("season") or "")[:20] or None,
                    cut=cut,
                    usage=str(row.get("usage") or "")[:30] or None,
                    source_dataset="fnauman/fashion-second-hand-front-only-rgb",
                    stock=1,
                )
                session.add(product)
                await session.flush()

                # Save product image from dataset
                try:
                    img_data = row.get("image")
                    if img_data is not None:
                        img_filename = f"{product.id.hex}.webp"
                        img_path = uploads_dir / img_filename
                        # Convert PIL image to RGB and save as WebP
                        if hasattr(img_data, "convert"):
                            img_data.convert("RGB").save(
                                str(img_path), "WEBP", quality=85
                            )
                            product.image_urls = [f"/uploads/dataset/{img_filename}"]
                except Exception:
                    logger.warning("Failed to save image for product %s", product.id)

                # Add English translation from dataset text
                if text:
                    session.add(ProductTranslation(
                        product_id=product.id,
                        language_code="en",
                        name=f"{brand} {type_name}",
                        description=text[:2000],
                    ))
                    await session.flush()

                inserted += 1
                if inserted % 20 == 0:
                    await session.commit()
                    logger.info("Inserted %d/%d products …", inserted, total)

            except Exception:
                errors += 1
                logger.exception("Error on row %d", i)
                if errors > 10:
                    logger.error("Too many errors, aborting.")
                    raise

        # Final commit
        await session.commit()
        logger.info("Done! Inserted %d products (%d errors).", inserted, errors)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parser = argparse.ArgumentParser(description="Seed TiendaVirtual with HuggingFace dataset")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to insert")
    parser.add_argument("--batch-size", type=int, default=100, help="Insert batch size")
    args = parser.parse_args()

    asyncio.run(seed(limit=args.limit, batch_size=args.batch_size))


if __name__ == "__main__":
    main()
