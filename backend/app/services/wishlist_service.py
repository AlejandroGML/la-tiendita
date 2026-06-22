"""WishlistService — business logic for user wishlist / favourites CRUD.

All operations are user-scoped. Duplicate adds are handled idempotently.
Stateless — session injected per-call.
"""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductTranslation
from app.models.wishlist import Wishlist
from app.repositories.wishlist_repository import WishlistRepository
from app.schemas.wishlist import WishlistItemResponse, WishlistResponse

logger = logging.getLogger(__name__)


class WishlistService:
    """Encapsulates wishlist business logic."""

    def __init__(
        self,
        wishlist_repo: WishlistRepository | None = None,
    ) -> None:
        self._wishlist_repo = wishlist_repo or WishlistRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_wishlist(
        self, session: AsyncSession, user_id: UUID
    ) -> WishlistResponse:
        """Return the authenticated user's wishlist with resolved product data.

        Eager-loads product translations so names can be resolved without
        N+1 queries.
        """
        items = await self._wishlist_repo.get_by_user(session, user_id)

        return WishlistResponse(
            items=[self._build_item(w) for w in items]
        )

    async def add_item(
        self, session: AsyncSession, user_id: UUID, product_id: UUID
    ) -> WishlistResponse:
        """Add a product to the wishlist — idempotent.

        If the product is already wishlisted, returns 200 with current state
        (no error). Raises ``ValueError`` for non-existent product IDs.
        """
        product = await session.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} not found")

        created = await self._wishlist_repo.upsert(
            session, user_id, product_id
        )

        return await self.get_wishlist(session, user_id)

    async def remove_item(
        self, session: AsyncSession, user_id: UUID, product_id: UUID
    ) -> None:
        """Remove a product from the wishlist.

        Raises ``ValueError`` if the item was not in the wishlist.
        """
        deleted = await self._wishlist_repo.remove(
            session, user_id, product_id
        )
        if not deleted:
            raise ValueError(f"Product {product_id} not in wishlist")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_product_name(product: Product) -> str:
        """Extract the best available name from product translations.

        Prefers Spanish (default locale), falls back to English or the
        first available translation.
        """
        translations: list[ProductTranslation] = product.translations  # type: ignore[assignment]
        if not translations:
            return "Unknown product"

        for t in translations:
            if t.language_code == "es":
                return t.name
        for t in translations:
            if t.language_code == "en":
                return t.name
        return translations[0].name

    @classmethod
    def _build_item(cls, wish: Wishlist) -> WishlistItemResponse:
        """Convert a Wishlist ORM instance to a response DTO."""
        image_urls: list = wish.product.image_urls  # type: ignore[assignment]
        return WishlistItemResponse(
            product_id=wish.product_id,
            name=cls._resolve_product_name(wish.product),
            price=str(wish.product.price),
            image_url=image_urls[0] if image_urls else None,
            slug=wish.product.slug,
            added_at=wish.added_at,
        )
