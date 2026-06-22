#!/usr/bin/env python3
"""Seed TiendaVirtual from HF dataset — zero RAM blowup.

Streams the dataset, processes ONE row at a time, saves images as raw JPEG
bytes, commits every 20 rows.  Never holds more than one image in memory.

Usage::

    cd backend
    python scripts/seed_parquet.py [--limit N]
"""

import argparse
import asyncio
import gc
import logging
import sys
import uuid
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets import load_dataset
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.engine import async_session as _async_session_fn
from app.models.category import Category, CategoryTranslation
from app.models.product import Product, ProductCondition, ProductTranslation
from app.services.slug_service import SlugService

logger = logging.getLogger("seed_parquet")

HF_DATASET = "fnauman/fashion-second-hand-front-only-rgb"
KNOWN_TYPES: set[str] = {
    "Top", "T-shirt", "Dress", "Sweater", "Shirt", "Blouse",
    "Blazer", "Tank Top", "Skirt", "Pants", "Jeans", "Jacket",
    "Coat", "Vest", "Shorts", "Jumpsuit", "Playsuit", "Cardigan",
    "Tunic", "Poncho", "Scarf", "Hat", "Belt", "Bag", "Shoes",
    "Boots", "Sandals", "Sneakers", "Heels", "Accessories",
}
PRICE_RANGE_MAP: dict[str, Decimal] = {
    "<50": Decimal("25.00"), "50-100": Decimal("75.00"),
    "100-150": Decimal("125.00"), "150-200": Decimal("175.00"),
    "200-250": Decimal("225.00"), "250-300": Decimal("275.00"),
    ">300": Decimal("350.00"),
}
CONDITION_MAP: dict[int, ProductCondition] = {
    1: ProductCondition.NEW, 2: ProductCondition.LIKE_NEW,
    3: ProductCondition.GOOD, 4: ProductCondition.FAIR, 5: ProductCondition.FAIR,
}


# ── Helpers ─────────────────────────────────────────────────────────────

def parse_price(price_str: str | None) -> Decimal:
    return PRICE_RANGE_MAP.get(price_str, Decimal("50.00")) if price_str else Decimal("50.00")

def map_condition(ci: int | None) -> tuple[ProductCondition | None, int | None]:
    if ci is None: return None, None
    r = max(1, min(5, int(ci)))
    return CONDITION_MAP.get(r), r

def parse_list(raw: str | None) -> list | None:
    if raw in (None, "[]", ""): return None
    import ast
    try:
        p = ast.literal_eval(raw)
        return p if isinstance(p, list) and len(p) > 0 else None
    except (ValueError, SyntaxError): return None

def build_condition_details(pilling, damage, stains, holes, smell) -> dict | None:
    d: dict = {}
    if pilling is not None: d["pilling"] = int(pilling)
    if damage and damage != "null": d["damage"] = damage
    if stains and stains not in ("No", "null"): d["stains"] = stains
    if holes and holes not in ("No", "null"): d["holes"] = holes
    if smell and smell != "null": d["smell"] = smell
    return d or None


# Spanish translations for each category type in the seed data
CATEGORY_ES: dict[str, str] = {
    "Accessories": "Accesorios",
    "Bag": "Bolso",
    "Belt": "Cinturón",
    "Blazer": "Blazer",
    "Blouse": "Blusa",
    "Boots": "Botas",
    "Cardigan": "Cárdigan",
    "Coat": "Abrigo",
    "Dress": "Vestido",
    "Hat": "Sombrero",
    "Heels": "Tacones",
    "Jacket": "Chaqueta",
    "Jeans": "Vaqueros",
    "Jumpsuit": "Mono",
    "Pants": "Pantalones",
    "Playsuit": "Mono",
    "Poncho": "Poncho",
    "Sandals": "Sandalias",
    "Scarf": "Bufanda",
    "Shirt": "Camisa",
    "Shoes": "Zapatos",
    "Shorts": "Pantalones Cortos",
    "Skirt": "Falda",
    "Sneakers": "Zapatillas",
    "Sweater": "Suéter",
    "T-shirt": "Camiseta",
    "Tank Top": "Top sin Mangas",
    "Top": "Top",
    "Tunic": "Túnica",
    "Vest": "Chaleco",
}

# ── Categories ──────────────────────────────────────────────────────────

async def ensure_categories(session: AsyncSession) -> dict[str, int]:
    result = await session.execute(
        select(Category).options(selectinload(Category.translations))
    )
    existing: dict[str, int] = {}
    for cat in result.scalars():
        for ct in cat.translations:
            if ct.language_code == "en": existing[ct.name] = cat.id; break
    mapping: dict[str, int] = {}
    for t in sorted(KNOWN_TYPES):
        if t in existing: mapping[t] = existing[t]; continue
        cat = Category(slug=SlugService.slugify(t))
        session.add(cat); await session.flush()
        session.add(CategoryTranslation(category_id=cat.id, language_code="en", name=t))
        session.add(CategoryTranslation(category_id=cat.id, language_code="es", name=CATEGORY_ES.get(t, t)))
        await session.flush(); mapping[t] = cat.id
    await session.commit()
    return mapping


# ── Main ────────────────────────────────────────────────────────────────

async def seed(limit: int | None = 200) -> None:
    uploads_dir = Path("/app/uploads/dataset")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Images → %s", uploads_dir)

    # Phase 1 — categories (single session)
    async with _async_session_fn() as session:
        cat_map = await ensure_categories(session)

    # Phase 2 — stream & insert (single session, no accumulation)
    logger.info("Loading %s (streaming) …", HF_DATASET)
    ds = load_dataset(HF_DATASET, split="train", streaming=True)
    inserted = errors = 0

    async with _async_session_fn() as session:
        for i, row in enumerate(ds):
            if limit and inserted >= limit:
                break
            try:
                type_name = str(row.get("type") or "Unknown")
                brand = str(row.get("brand") or "Unknown Brand")[:100]
                text = str(row.get("text") or "").strip()

                slug = SlugService.slugify(f"{brand} {type_name}")
                existing = await session.execute(
                    select(Product.id).where(Product.slug == slug)
                )
                if existing.scalar_one_or_none():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                product = Product(
                    slug=slug,
                    price=parse_price(row.get("price")),
                    category_id=cat_map.get(type_name),
                    brand=brand,
                    condition=map_condition(row.get("condition"))[0],
                    condition_rating=map_condition(row.get("condition"))[1],
                    condition_details=build_condition_details(
                        row.get("pilling"), str(row.get("damage","") or ""),
                        str(row.get("stains","") or ""), str(row.get("holes","") or ""),
                        str(row.get("smell","") or ""),
                    ),
                    target_gender=str(row.get("category") or "")[:20] or None,
                    material=str(row.get("material") or "")[:255] or None,
                    colors=parse_list(str(row.get("colors", ""))),
                    trend=str(row.get("trend") or "")[:50] or None,
                    pattern=str(row.get("pattern") or "")[:50] or None,
                    season=str(row.get("season") or "")[:20] or None,
                    cut=parse_list(str(row.get("cut", ""))),
                    usage=str(row.get("usage") or "")[:30] or None,
                    source_dataset=HF_DATASET,
                )
                session.add(product)
                await session.flush()

                # ── Save image — ONE at a time, immediate cleanup ──
                img = row.get("image")
                if img is not None:
                    img_path = uploads_dir / f"{product.id.hex}.jpg"
                    try:
                        if img.mode in ("RGBA", "LA", "P"):
                            img = img.convert("RGB")
                        img.save(str(img_path), "JPEG", quality=85)
                        product.image_urls = [f"/uploads/dataset/{product.id.hex}.jpg"]
                    except Exception:
                        logger.warning("Image save failed for %s", product.id)

                if text:
                    session.add(ProductTranslation(
                        product_id=product.id, language_code="en",
                        name=f"{brand} {type_name}", description=text[:2000],
                    ))
                    await session.flush()

                inserted += 1

                if inserted % 20 == 0:
                    await session.commit()
                    gc.collect()
                    logger.info("Inserted %d products …", inserted)

            except Exception:
                errors += 1
                logger.exception("Error on product")
                if errors > 10: raise

        await session.commit()
        gc.collect()

    logger.info("Done! %d products inserted (%d errors)", inserted, errors)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(seed(limit=args.limit))


if __name__ == "__main__":
    main()
