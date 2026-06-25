"""Product response serializer.

Extracted verbatim from ``app.controllers.products._build_product_response``
so the service-layer cache-aside path can build the same dict shape the
public controllers return. Keeping the logic in one place guarantees the
cached value is byte-identical to the live response.
"""

from __future__ import annotations


def build_product_response(
    product, *, lang: str | None = None, promotion_info: dict | None = None
) -> dict:
    """Convert a Product ORM instance to a dict, optionally filtering
    translations to *lang* with ``en`` fallback.

    When *promotion_info* is provided (keyed by ``product.id``),
    ``sale_price``, ``discount_label``, and ``promotion`` summary fields
    are attached to the response.
    """
    translations = [
        {
            "language_code": t.language_code,
            "name": t.name,
            "description": t.description,
        }
        for t in product.translations
    ]

    if lang is not None:
        # Find translation for requested lang, fallback to en, then first
        matched = next(
            (t for t in translations if t["language_code"] == lang), None
        )
        if matched is None:
            matched = next(
                (t for t in translations if t["language_code"] == "en"), None
            )
        if matched is None and translations:
            matched = translations[0]
        translations = [matched] if matched else []

    # Serialize variants (non-deleted only)
    variants = [
        {
            "id": str(v.id),
            "product_id": str(v.product_id),
            "size": v.size.value if v.size else None,
            "color": v.color,
            "color_hex": v.color_hex,
            "stock": v.stock,
            "sku": v.sku,
        }
        for v in getattr(product, "variants", []) or []
        if v.deleted_at is None
    ]

    # Sale pricing from resolved promotions
    _sale_price = None
    _discount_label = None
    _promotion_summary = None

    if promotion_info and product.id in promotion_info:
        info = promotion_info[product.id]
        promo = info["promotion"]
        _sale_price = str(info["sale_price"])
        _discount_label = info.get("discount_label") or None
        _promotion_summary = {
            "code": promo.code,
            "discount_percent": promo.discount_percent,
            "end_date": promo.end_date.isoformat() if promo.end_date else None,
        }

    return {
        "id": str(product.id),
        "slug": product.slug,
        "price": str(product.price),
        "category_id": product.category_id,
        "brand": product.brand,
        "condition": product.condition.value if product.condition else None,
        "condition_rating": product.condition_rating,
        "condition_details": product.condition_details,
        "target_gender": product.target_gender,
        "material": product.material,
        "colors": product.colors,
        "trend": product.trend,
        "pattern": product.pattern,
        "season": product.season,
        "cut": product.cut,
        "usage": product.usage,
        "source_dataset": product.source_dataset,
        "image_urls": product.image_urls,
        "translations": translations,
        "variants": variants,
        "variant_count": len(variants),
        "created_at": product.created_at.isoformat(),
        "sale_price": _sale_price,
        "discount_label": _discount_label,
        "promotion": _promotion_summary,
    }
