#!/usr/bin/env python3
"""Generate 500 fake fashion products with ES/EN/SV translations. No external downloads."""

import asyncio
import logging
import random
import uuid
from decimal import Decimal
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.db.engine import async_session
from app.models.product import Product, ProductCondition, ProductTranslation
from app.models.category import Category, CategoryTranslation
from app.services.slug_service import SlugService

logger = logging.getLogger("seed_500")

# ── DATA ────────────────────────────────────────────────────────────────────

CATEGORIES = {
    "T-shirt": {"es": "Camiseta", "sv": "T-shirt"},
    "Top": {"es": "Top", "sv": "Topp"},
    "Blouse": {"es": "Blusa", "sv": "Blus"},
    "Shirt": {"es": "Camisa", "sv": "Skjorta"},
    "Tank Top": {"es": "Top sin Mangas", "sv": "Linne"},
    "Sweater": {"es": "Suéter", "sv": "Tröja"},
    "Cardigan": {"es": "Cárdigan", "sv": "Cardigan"},
    "Blazer": {"es": "Blazer", "sv": "Kavaj"},
    "Jacket": {"es": "Chaqueta", "sv": "Jacka"},
    "Coat": {"es": "Abrigo", "sv": "Rock"},
    "Vest": {"es": "Chaleco", "sv": "Väst"},
    "Dress": {"es": "Vestido", "sv": "Klänning"},
    "Skirt": {"es": "Falda", "sv": "Kjol"},
    "Pants": {"es": "Pantalones", "sv": "Byxor"},
    "Jeans": {"es": "Vaqueros", "sv": "Jeans"},
    "Shorts": {"es": "Pantalones Cortos", "sv": "Shorts"},
    "Jumpsuit": {"es": "Mono", "sv": "Hoppdress"},
    "Tunic": {"es": "Túnica", "sv": "Tunika"},
    "Poncho": {"es": "Poncho", "sv": "Poncho"},
    "Scarf": {"es": "Bufanda", "sv": "Sjal"},
    "Hat": {"es": "Sombrero", "sv": "Hatt"},
    "Bag": {"es": "Bolso", "sv": "Väska"},
    "Belt": {"es": "Cinturón", "sv": "Bälte"},
    "Shoes": {"es": "Zapatos", "sv": "Skor"},
    "Sneakers": {"es": "Zapatillas", "sv": "Sneakers"},
    "Boots": {"es": "Botas", "sv": "Kängor"},
    "Sandals": {"es": "Sandalias", "sv": "Sandaler"},
    "Heels": {"es": "Tacones", "sv": "Klackskor"},
}

BRANDS = [
    "Zara", "H&M", "Mango", "Pull&Bear", "Bershka", "Stradivarius",
    "Uniqlo", "Adidas", "Nike", "Puma", "Levi's", "Tommy Hilfiger",
    "Calvin Klein", "Jack & Jones", "Vero Moda", "Only", "S.Oliver",
    "Gina Tricot", "Bikbok", "KappAhl", "Lindex", "Weekday", "Monki",
    "COS", "Arket", "& Other Stories", "NA-KD", "Cubus", "New Yorker",
]

COLORS_EN = ["Black", "White", "Red", "Blue", "Green", "Yellow", "Pink",
             "Gray", "Brown", "Beige", "Navy", "Burgundy", "Purple", "Orange", "Cream"]
COLORS_ES = ["Negro", "Blanco", "Rojo", "Azul", "Verde", "Amarillo", "Rosa",
             "Gris", "Marrón", "Beige", "Navy", "Burdeos", "Lila", "Naranja", "Crema"]
COLORS_SV = ["Svart", "Vit", "Röd", "Blå", "Grön", "Gul", "Rosa",
             "Grå", "Brun", "Beige", "Mörkblå", "Bourgogne", "Lila", "Orange", "Grädde"]

MATERIALS_EN = ["Cotton", "Polyester", "Wool", "Silk", "Linen", "Viscose", "Nylon",
                "Denim", "Leather", "Cashmere", "Velvet", "Suede", "Knit", "Lace"]
MATERIALS_ES = ["Algodón", "Poliéster", "Lana", "Seda", "Lino", "Viscosa", "Nailon",
                "Denim", "Cuero", "Cashmere", "Terciopelo", "Gamuza", "Punto", "Encaje"]
MATERIALS_SV = ["Bomull", "Polyester", "Ull", "Silke", "Linne", "Visikos", "Nylon",
                "Denim", "Läder", "Cashmere", "Sammet", "Mocka", "Stickat", "Spets"]

SIZES = ["XS", "S", "M", "L", "XL"]
CONDITIONS = [("new", 5), ("like_new", 4), ("good", 3), ("good", 3), ("fair", 2)]

DESCS_EN = {
    "T-shirt": "Classic cotton t-shirt. Comfortable and durable for everyday wear.",
    "Dress": "Beautiful dress for any occasion. Flattering and elegant design.",
    "Jacket": "Stylish jacket to complete your look. Perfect for layering.",
    "Jeans": "Classic jeans with the perfect fit. Durable denim fabric.",
    "Shoes": "Comfortable shoes for everyday wear. Great quality and style.",
    "Bag": "Spacious and stylish bag. Perfect for everyday use.",
    "Sweater": "Cozy sweater for cooler weather. Soft and warm.",
    "Coat": "Warm and elegant coat. Timeless design for cold days.",
    "Blouse": "Elegant blouse with a feminine touch. Perfect for work or special occasions.",
    "Skirt": "Versatile skirt that pairs with anything. Classic wardrobe staple.",
}
DESCS_ES = {
    "T-shirt": "Camiseta clásica de algodón. Cómoda y duradera para el día a día.",
    "Dress": "Vestido hermoso para cualquier ocasión. Diseño elegante y favorecedor.",
    "Jacket": "Chaqueta moderna para completar tu look. Perfecta para capas.",
    "Jeans": "Vaqueros clásicos con el ajuste perfecto. Tela denim duradera.",
    "Shoes": "Zapatos cómodos para uso diario. Gran calidad y estilo.",
    "Bag": "Bolso espacioso y elegante. Perfecto para el uso diario.",
    "Sweater": "Suéter acogedor para clima frío. Suave y cálido.",
    "Coat": "Abrigo cálido y elegante. Diseño atemporal para días fríos.",
    "Blouse": "Blusa elegante con un toque femenino. Perfecta para el trabajo u ocasiones especiales.",
    "Skirt": "Falda versátil que combina con todo. Prenda clásica de guardarropa.",
}
DESCS_SV = {
    "T-shirt": "Klassisk bomullströja. Bekväm och slitstark för vardagsbruk.",
    "Dress": "Vacker klänning för alla tillfällen. Elegant och smickrande design.",
    "Jacket": "Modern jacka som kompletterar din look. Perfekt för lager-på-lager.",
    "Jeans": "Klassiska jeans med perfekt passform. Hållbart denimmaterial.",
    "Shoes": "Bekväma skor för vardagsbruk. Hög kvalitet och stil.",
    "Bag": "Rymlig och stilfull väska. Perfekt för vardagsbruk.",
    "Sweater": "Mysig tröja för kallare väder. Mjuk och varm.",
    "Coat": "Varm och elegant rock. Tidlös design för kalla dagar.",
    "Blouse": "Elegant blus med en feminin touch. Perfekt för jobb eller speciella tillfällen.",
    "Skirt": "Mångsidig kjol som passar till allt. Klassisk garderobsstandard.",
}


def desc_for(cat, lang):
    d = {"en": DESCS_EN, "es": DESCS_ES, "sv": DESCS_SV}[lang]
    return d.get(cat, f"Second-hand {cat.lower()} in excellent condition. Modern and versatile.")


async def seed(limit=500, batch=50):
    async with async_session() as session:
        # Clean existing data
        await session.execute(delete(ProductTranslation))
        await session.execute(delete(Product))
        await session.execute(delete(CategoryTranslation))
        await session.execute(delete(Category))
        await session.flush()

        # Create categories
        cat_map = {}
        for en_name, trans in CATEGORIES.items():
            slug = SlugService.slugify(en_name)
            cat = Category(slug=slug)
            session.add(cat)
            await session.flush()
            for lang, name in [("en", en_name), ("es", trans["es"]), ("sv", trans["sv"])]:
                session.add(CategoryTranslation(category_id=cat.id, language_code=lang, name=name))
            await session.flush()
            cat_map[en_name] = cat.id

        await session.commit()
        logger.info("Created %d categories", len(cat_map))

        # Generate products
        cat_keys = list(CATEGORIES.keys())
        inserted = 0
        for i in range(limit):
            try:
                cat = random.choice(cat_keys)
                brand = random.choice(BRANDS)
                color_idx = random.randint(0, len(COLORS_EN) - 1)
                color_en = COLORS_EN[color_idx]
                color_es = COLORS_ES[color_idx]
                color_sv = COLORS_SV[color_idx]
                mat_idx = random.randint(0, len(MATERIALS_EN) - 1)
                material_en = MATERIALS_EN[mat_idx]
                material_es = MATERIALS_ES[mat_idx]
                material_sv = MATERIALS_SV[mat_idx]
                cond_str, cond_rating = random.choice(CONDITIONS)
                price = Decimal(str(round(random.uniform(15, 350), 2)))
                stock = random.randint(1, 15)
                size = random.choice(SIZES)
                gender = random.choice(["female", "male", "unisex", "female", "female"])

                slug = SlugService.slugify(f"{brand}-{cat}-{uuid.uuid4().hex[:6]}")

                # 70% brand name, 30% color name
                if random.random() > 0.3:
                    en_name = f"{brand} {cat}"
                    es_name = f"{brand} {CATEGORIES[cat]['es']}"
                    sv_name = f"{brand} {CATEGORIES[cat]['sv']}"
                else:
                    en_name = f"{color_en} {cat}"
                    es_name = f"{color_es} {CATEGORIES[cat]['es']}"
                    sv_name = f"{color_sv} {CATEGORIES[cat]['sv']}"

                # Sometimes use material
                if random.random() > 0.6:
                    en_name = f"{material_en} {cat}"
                    es_name = f"{material_es} {CATEGORIES[cat]['es']}"
                    sv_name = f"{material_sv} {CATEGORIES[cat]['sv']}"

                product = Product(
                    slug=slug, price=price,
                    category_id=cat_map[cat], brand=brand, material=material_en,
                    condition=ProductCondition(cond_str),
                    condition_rating=cond_rating,
                    colors=[color_en, color_es] if random.random() > 0.5 else [color_en],
                    target_gender=gender,
                    season=random.choice([None, "spring", "summer", "autumn", "winter"]),
                    source_dataset="generated-500",
                )
                session.add(product)
                await session.flush()

                session.add(ProductTranslation(product_id=product.id, language_code="en", name=en_name[:255], description=desc_for(cat, "en")[:2000]))
                session.add(ProductTranslation(product_id=product.id, language_code="es", name=es_name[:255], description=desc_for(cat, "es")[:2000]))
                session.add(ProductTranslation(product_id=product.id, language_code="sv", name=sv_name[:255], description=desc_for(cat, "sv")[:2000]))

                inserted += 1
                if inserted % batch == 0:
                    await session.commit()
                    logger.info("Inserted %d/%d products", inserted, limit)

            except Exception as e:
                logger.warning("Error on product %d: %s", i, e)
                if i > 10:
                    raise
                continue

        await session.commit()
        logger.info("DONE! %d products across %d categories.", inserted, len(cat_map))


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(seed(limit=500))

if __name__ == "__main__":
    main()
