"""SlugService — stateless slug generation for ProductService.

Provides URL-safe slug generation from human-readable names with
NFKD normalisation, collision resolution via DB lookup, and
configurable max slug length.
"""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class SlugService:
    """Stateless slug generation utility.

    Slugs are generated from product names using NFKD normalisation,
    with collision resolution by appending numeric suffixes.
    """

    MAX_SLUG_LEN = 200

    @staticmethod
    def slugify(name: str) -> str:
        """Convert a human-readable name into a URL-safe slug.

        Uses NFKD normalisation to strip accents from Spanish characters
        (e.g. "cañón" → "canon"), then lowercases and replaces runs of
        non-alphanumeric characters with a single hyphen.
        """
        nfkd = unicodedata.normalize("NFKD", name)
        ascii_text = nfkd.encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
        return slug or "producto"

    async def generate_slug(
        self, session: AsyncSession, name: str
    ) -> str:
        """Generate a unique slug from *name*, resolving collisions by
        appending a numeric suffix (``-2``, ``-3``, …).

        Slugs are truncated to ``MAX_SLUG_LEN`` (200) to prevent
        database insertion failures on the ``String(200)`` column.
        Collision suffixes fit within the limit by shrinking the base.

        Example: "Chaqueta Denim" → "chaqueta-denim". If that slug is
        taken, tries "chaqueta-denim-2", and so on.
        """
        base = self.slugify(name)
        if len(base) > self.MAX_SLUG_LEN:
            base = base[: self.MAX_SLUG_LEN]
        slug = base
        attempt = 1

        while True:
            existing = await session.execute(
                select(Product.id).where(Product.slug == slug)
            )
            if existing.scalar_one_or_none() is None:
                return slug
            attempt += 1
            suffix = f"-{attempt}"
            # Shrink base so base + suffix ≤ MAX_SLUG_LEN
            available = self.MAX_SLUG_LEN - len(suffix)
            slug = f"{base[:available]}{suffix}"
