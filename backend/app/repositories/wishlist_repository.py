"""WishlistRepository — encapsulates Wishlist data access.

Standalone repository (not ``BaseRepository``) because ``Wishlist`` inherits
``_CompositeBase``, not ``Base`` — the ``ModelT`` bound on
``BaseRepository`` requires models with a UUID surrogate PK.

The service retains product existence validation and response DTO
construction.
"""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductTranslation
from app.models.wishlist import Wishlist


class WishlistRepository:
    """Wishlist data access — composite-key CRUD, no BaseRepository dependency.

    Usage::

        repo = WishlistRepository()
        items = await repo.get_by_user(session, user_id, lang="es")
        ok = await repo.upsert(session, user_id, product_id)
    """

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        lang: str = "es",
    ) -> list[Wishlist]:
        """Return all wishlist entries for a user with product data.

        Eager-loads product translations so names can be resolved without
        N+1 queries.  Results ordered by most recently added.

        Args:
            session: Active async DB session.
            user_id: The user UUID.
            lang: Language code for translation loading (reserved).

        Returns:
            List of wishlist entries.
        """
        stmt = (
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .options(
                selectinload(Wishlist.product).selectinload(
                    Product.translations
                ),
            )
            .order_by(Wishlist.added_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    async def upsert(
        self,
        session: AsyncSession,
        user_id: UUID,
        product_id: UUID,
    ) -> bool:
        """Add a product to the user's wishlist — idempotent.

        Returns ``True`` if a new wishlist entry was created, ``False`` if
        the product was already wishlisted.

        Args:
            session: Active async DB session.
            user_id: The user UUID.
            product_id: The product UUID.

        Returns:
            ``True`` if created, ``False`` if already existed.
        """
        existing = await session.scalar(
            select(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.product_id == product_id,
            )
        )
        if existing is not None:
            return False

        wish = Wishlist(user_id=user_id, product_id=product_id)
        session.add(wish)
        await session.flush()
        return True

    async def remove(
        self,
        session: AsyncSession,
        user_id: UUID,
        product_id: UUID,
    ) -> bool:
        """Remove a product from the user's wishlist.

        Returns ``True`` if the entry was deleted, ``False`` if it did not
        exist.

        Args:
            session: Active async DB session.
            user_id: The user UUID.
            product_id: The product UUID.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        stmt = delete(Wishlist).where(
            Wishlist.user_id == user_id,
            Wishlist.product_id == product_id,
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0
