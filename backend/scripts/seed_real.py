#!/usr/bin/env python3
"""Seed 300 products from fnauman/fashion-second-hand-front-only-rgb with real data + images + 3-language translations."""

import asyncio, gc, logging, sys, os, uuid, random
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from app.db.engine import async_session
from app.config import settings
from app.models.product import Product, ProductCondition, ProductTranslation
from app.models.category import Category, CategoryTranslation
from app.services.slug_service import SlugService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_real")

# ── Translation mappings ─────────────────────────────────────────────────────

CAT_ES = {
    "Top": "Top", "T-shirt": "Camiseta", "Blouse": "Blusa", "Shirt": "Camisa",
    "Tank Top": "Top sin Mangas", "Sweater": "Suéter", "Cardigan": "Cárdigan",
    "Blazer": "Blazer", "Jacket": "Chaqueta", "Coat": "Abrigo", "Vest": "Chaleco",
    "Poncho": "Poncho", "Tunic": "Túnica", "Dress": "Vestido", "Skirt": "Falda",
    "Jumpsuit": "Mono", "Playsuit": "Mono", "Pants": "Pantalones", "Jeans": "Vaqueros",
    "Shorts": "Pantalones Cortos", "Belt": "Cinturón", "Scarf": "Bufanda",
    "Hat": "Sombrero", "Bag": "Bolso", "Shoes": "Zapatos", "Sneakers": "Zapatillas",
    "Boots": "Botas", "Sandals": "Sandalias", "Heels": "Tacones",
}
CAT_SV = {
    "Top": "Topp", "T-shirt": "T-shirt", "Blouse": "Blus", "Shirt": "Skjorta",
    "Tank Top": "Linne", "Sweater": "Tröja", "Cardigan": "Cardigan", "Blazer": "Kavaj",
    "Jacket": "Jacka", "Coat": "Rock", "Vest": "Väst", "Poncho": "Poncho", "Tunic": "Tunika",
    "Dress": "Klänning", "Skirt": "Kjol", "Jumpsuit": "Hoppdress", "Playsuit": "Lekdress",
    "Pants": "Byxor", "Jeans": "Jeans", "Shorts": "Shorts", "Belt": "Bälte",
    "Scarf": "Sjal", "Hat": "Hatt", "Bag": "Väska", "Shoes": "Skor",
    "Sneakers": "Sneakers", "Boots": "Kängor", "Sandals": "Sandaler", "Heels": "Klackskor",
}
COLOR_ES = {"Pink":"Rosa","Blue":"Azul","Black":"Negro","White":"Blanco","Red":"Rojo",
    "Green":"Verde","Yellow":"Amarillo","Gray":"Gris","Brown":"Marrón","Beige":"Beige",
    "Navy":"Navy","Burgundy":"Burdeos","Purple":"Lila","Orange":"Naranja","Cream":"Crema",
    "Khaki":"Caqui","Turquoise":"Turquesa","Gold":"Dorado","Silver":"Plateado","Multicolor":"Multicolor"}
COLOR_SV = {"Pink":"Rosa","Blue":"Blå","Black":"Svart","White":"Vit","Red":"Röd",
    "Green":"Grön","Yellow":"Gul","Gray":"Grå","Brown":"Brun","Beige":"Beige",
    "Navy":"Mörkblå","Burgundy":"Bourgogne","Purple":"Lila","Orange":"Orange","Cream":"Grädde",
    "Khaki":"Khaki","Turquoise":"Turkos","Gold":"Guld","Silver":"Silver","Multicolor":"Flerfärgad"}

PRICE_MAP = {"<50": Decimal("25.00"), "50-100": Decimal("75.00"), "100-150": Decimal("125.00"),
    "150-200": Decimal("175.00"), "200-250": Decimal("225.00"), "250-300": Decimal("275.00"), ">300": Decimal("350.00")}
COND_MAP = {1: ProductCondition.NEW, 2: ProductCondition.LIKE_NEW, 3: ProductCondition.GOOD, 4: ProductCondition.FAIR, 5: ProductCondition.FAIR}

DESCS_EN = {
    "Top": "Trendy top in great second-hand condition. Lightweight and comfortable for everyday styling.",
    "T-shirt": "Classic cotton t-shirt in excellent second-hand condition. Perfect for casual wear.",
    "Dress": "Beautiful dress in great pre-loved condition. Flattering and timeless design.",
    "Jacket": "Stylish jacket in good second-hand condition. Perfect for layering and everyday wear.",
    "Jeans": "Classic jeans in great pre-owned condition. Durable denim that fits perfectly.",
    "Shirt": "Smart shirt in excellent second-hand condition. Versatile piece for any wardrobe.",
    "Blouse": "Elegant blouse in great condition. Perfect for work or special occasions.",
    "Sweater": "Cozy sweater in good second-hand condition. Soft, warm and comfortable.",
    "Skirt": "Versatile skirt in great pre-loved condition. A timeless wardrobe staple.",
    "Coat": "Warm coat in excellent second-hand condition. Timeless design for cold days.",
    "Sneakers": "Casual sneakers in good pre-owned condition. Comfortable for daily wear.",
    "Bag": "Stylish bag in great second-hand condition. Perfect for everyday use.",
}
DESCS_ES = {
    "Top": "Top moderno en excelente condición de segunda mano. Ligero y cómodo para el día a día.",
    "T-shirt": "Camiseta clásica de algodón en excelente condición. Perfecta para uso casual.",
    "Dress": "Vestido hermoso en excelente condición. Diseño favorecedor y atemporal.",
    "Jacket": "Chaqueta moderna en buen estado. Perfecta para capas y uso diario.",
    "Jeans": "Vaqueros clásicos en excelente condición. Denim duradero con ajuste perfecto.",
    "Shirt": "Camisa elegante en excelente condición. Prenda versátil para cualquier guardarropa.",
    "Blouse": "Blusa elegante en excelente condición. Perfecta para el trabajo u ocasiones especiales.",
    "Sweater": "Suéter acogedor en buen estado. Suave, cálido y cómodo.",
    "Skirt": "Falda versátil en excelente condición. Una prenda clásica y atemporal.",
    "Coat": "Abrigo cálido en excelente condición. Diseño atemporal para días fríos.",
    "Sneakers": "Zapatillas casuales en buen estado. Cómodas para uso diario.",
    "Bag": "Bolso elegante en excelente condición. Perfecto para el uso diario.",
}
DESCS_SV = {
    "Top": "Modern topp i utmärkt andrahandsskick. Lätt och bekväm för vardagsbruk.",
    "T-shirt": "Klassisk bomullströja i utmärkt skick. Perfekt för avslappnad användning.",
    "Dress": "Vacker klänning i utmärkt begagnat skick. Smickrande och tidlös design.",
    "Jacket": "Modern jacka i gott begagnat skick. Perfekt för lager-på-lager och vardagsbruk.",
    "Jeans": "Klassiska jeans i utmärkt begagnat skick. Hållbart denimmaterial med perfekt passform.",
    "Shirt": "Smart skjorta i utmärkt begagnat skick. Mångsidigt plagg för alla garderober.",
    "Blouse": "Elegant blus i utmärkt skick. Perfekt för jobb eller speciella tillfällen.",
    "Sweater": "Mysig tröja i gott begagnat skick. Mjuk, varm och bekväm.",
    "Skirt": "Mångsidig kjol i utmärkt begagnat skick. En tidlös garderobsklassiker.",
    "Coat": "Varm rock i utmärkt begagnat skick. Tidlös design för kalla dagar.",
    "Sneakers": "Avslappnade sneakers i gott begagnat skick. Bekväma för dagligt bruk.",
    "Bag": "Stilfull väska i utmärkt begagnat skick. Perfekt för vardagsbruk.",
}

def desc_for(cat, lang):
    m = {"en": DESCS_EN, "es": DESCS_ES, "sv": DESCS_SV}[lang]
    return m.get(cat, f"Second-hand {cat.lower()} in excellent condition.")

async def seed(limit=300):
    from datasets import load_dataset
    from tqdm import tqdm
    from PIL import Image as PILImage

    ds = load_dataset("fnauman/fashion-second-hand-front-only-rgb", split="train", streaming=True)
    uploaded = 0

    async with async_session() as session:
        # ── Clean DB ───────────────────────────────────────────────────────
        await session.execute(delete(ProductTranslation))
        await session.execute(delete(Product))
        await session.execute(delete(CategoryTranslation))
        await session.execute(delete(Category))
        await session.commit()
        logger.info("🧹 DB cleaned")

        # ── Collect types from dataset ─────────────────────────────────────
        all_types = set()
        rows = []
        for row in ds:
            t = str(row.get("type") or "Unknown").strip()
            if t:
                all_types.add(t)
            rows.append(row)
            if len(rows) >= limit:
                break
        logger.info(f"📦 Loaded {len(rows)} rows, {len(all_types)} categories")

        # ── Create categories ──────────────────────────────────────────────
        cat_map = {}
        for en_name in sorted(all_types):
            slug = SlugService.slugify(en_name)
            cat = Category(slug=slug)
            session.add(cat); await session.flush()
            session.add(CategoryTranslation(category_id=cat.id, language_code="en", name=en_name))
            session.add(CategoryTranslation(category_id=cat.id, language_code="es", name=CAT_ES.get(en_name, en_name)))
            session.add(CategoryTranslation(category_id=cat.id, language_code="sv", name=CAT_SV.get(en_name, en_name)))
            await session.flush()
            cat_map[en_name] = cat.id
        await session.commit()
        logger.info(f"🏷️  Created {len(cat_map)} categories")

        # ── Upload directory ───────────────────────────────────────────────
        upload_dir = Path(settings.UPLOAD_DIR) / "products"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # ── Insert products ────────────────────────────────────────────────
        inserted = 0
        pbar = tqdm(total=len(rows), desc="📦 Products", unit="prod")

        for i, row in enumerate(rows):
            try:
                type_name = str(row.get("type") or "Unknown").strip()
                if type_name not in cat_map:
                    continue

                # Extract real data from dataset
                brand = str(row.get("brand") or "Unknown")[:100]
                if brand == "None": brand = "Unknown"
                colors_raw = row.get("colors") or []
                colors_en = [str(c) for c in colors_raw if c] if isinstance(colors_raw, list) else []
                if not colors_en:
                    colors_en = ["Multicolor"]
                color_en = colors_en[0]  # primary color

                # Price: dataset has ranges like "<50", "50-100", etc.
                price_str = str(row.get("price") or "")
                price = PRICE_MAP.get(price_str, Decimal("50.00"))

                # Condition
                cond_int = row.get("condition")
                if cond_int is not None and isinstance(cond_int, (int, float)):
                    condition = COND_MAP.get(int(cond_int), ProductCondition.GOOD)
                    rating = max(1, min(5, int(cond_int)))
                else:
                    condition, rating = ProductCondition.GOOD, 3

                # Material
                material = str(row.get("material") or "")[:255]
                if material == "None" or not material:
                    material = None

                # Gender
                gender_raw = str(row.get("category") or "").strip().lower()
                if gender_raw in ("ladies", "woman", "female", "girls"):
                    target_gender = "female"
                elif gender_raw in ("men", "man", "male", "boys"):
                    target_gender = "male"
                else:
                    target_gender = "unisex"

                # Other fields
                trend = str(row.get("trend") or "")[:50] or None
                pattern = str(row.get("pattern") or "")[:50] or None
                season = str(row.get("season") or "")[:20] or None

                # Generate unique slug
                slug = SlugService.slugify(f"{brand}-{type_name}")
                # Check uniqueness
                existing = await session.execute(select(Product.id).where(Product.slug == slug))
                if existing.scalar_one_or_none():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # Create product
                product = Product(
                    slug=slug, price=price, category_id=cat_map[type_name],
                    brand=brand, material=material,
                    condition=condition, condition_rating=rating,
                    colors=colors_en, target_gender=target_gender,
                    trend=trend, pattern=pattern, season=season,
                    source_dataset="fnauman/fashion-second-hand",
                )
                session.add(product)
                await session.flush()

                # ── Save image from dataset ────────────────────────────────
                img_data = row.get("image")
                if img_data is not None and hasattr(img_data, "convert"):
                    img_path = upload_dir / f"{product.id.hex}.webp"
                    try:
                        img_data.convert("RGB").save(str(img_path), "WEBP", quality=85)
                        product.image_urls = [f"/uploads/products/{product.id.hex}.webp"]
                    except Exception:
                        logger.warning(f"  ⚠️ Image save failed for {slug}")
                else:
                    logger.warning(f"  ⚠️ No image for {slug}")

                # ── Generate 3-language translations ──────────────────────
                en_name = f"{brand} {type_name}"
                es_name = f"{brand} {CAT_ES.get(type_name, type_name)}"
                sv_name = f"{brand} {CAT_SV.get(type_name, type_name)}"

                # If a color is available, use it for variety
                if color_en and color_en in COLOR_ES and color_en in COLOR_SV:
                    if random.random() > 0.4:
                        en_name = f"{color_en} {type_name}"
                        es_name = f"{COLOR_ES[color_en]} {CAT_ES.get(type_name, type_name)}"
                        sv_name = f"{COLOR_SV[color_en]} {CAT_SV.get(type_name, type_name)}"

                # Description
                text = str(row.get("text") or "")
                en_desc = text[:2000] if text and text != "None" else desc_for(type_name, "en")[:2000]

                session.add(ProductTranslation(product_id=product.id, language_code="en", name=en_name[:255], description=en_desc))
                session.add(ProductTranslation(product_id=product.id, language_code="es", name=es_name[:255], description=desc_for(type_name, "es")[:2000]))
                session.add(ProductTranslation(product_id=product.id, language_code="sv", name=sv_name[:255], description=desc_for(type_name, "sv")[:2000]))

                inserted += 1
                if inserted % 30 == 0:
                    await session.commit()
                    gc.collect()

            except Exception as e:
                logger.warning(f"⚠️ Error row {i}: {e}")
                await session.rollback()
                continue

            pbar.update(1)

        await session.commit()
        pbar.close()
        logger.info(f"\n✅ DONE! {inserted} products with real data + images + 3 languages.")

        # ── Verify ──────────────────────────────────────────────────────────
        result = await session.execute(select(Product))
        all_p = result.scalars().all()
        with_img = sum(1 for p in all_p if p.image_urls and len(p.image_urls) > 0 and p.image_urls[0])
        logger.info(f"Images: {with_img}/{len(all_p)} products have images")

asyncio.run(seed(limit=300))
