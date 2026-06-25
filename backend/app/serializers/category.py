"""Category response serializers.

Extracted verbatim from ``app.controllers.categories`` so the public
controller and any future service layer share a single serialization path.
"""

from __future__ import annotations

from app.models.category import Category


def build_category_response(category: Category) -> dict:
    """Convert a Category ORM instance to a full response dict with all
    translations."""
    return {
        "id": category.id,
        "slug": category.slug,
        "image_url": category.image_url,
        "translations": [
            {
                "language_code": t.language_code,
                "name": t.name,
            }
            for t in category.translations
        ],
    }


def build_category_list_item(category: Category, lang: str) -> dict:
    """Convert a Category to a list-item dict with translated name.

    Falls back to ``en``, then the first available translation if the
    requested language is missing."""
    translations = {
        t.language_code: t.name for t in category.translations
    }
    name = translations.get(lang) or translations.get("en")
    if name is None and translations:
        name = next(iter(translations.values()))

    return {
        "id": category.id,
        "slug": category.slug,
        "name": name or "",
    }
