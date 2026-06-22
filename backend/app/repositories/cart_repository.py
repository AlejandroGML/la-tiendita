"""CartRepository — encapsulates CartItem data access.

Extracts all SQLAlchemy queries from ``CartService`` into a dedicated
repository.  The service retains scope validation, stock checks, promotion
resolution, and response DTO construction.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ColumnElement, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.product import Product, ProductTranslation
from app.models.product_variant import ProductVariant
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[CartItem]):
    """CartItem-specific data access — dual-scope (user or session).

    Usage::

        repo = CartRepository()
        items = await repo.get_items(session, user_id=user_uuid)
        item = await repo.upsert_item(session, user_id=uid, product_id=pid, ...)
    """

    def __init__(self) -> None:
        super().__init__(CartItem)

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scope_filter(
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> ColumnElement[bool]:
        """Return a SQLAlchemy WHERE clause for the active scope.

        Args:
            user_id: Scope to a registered user.
            session_id: Scope to an anonymous session.

        Returns:
            A filter expression matching ``CartItem.user_id`` or
            ``CartItem.session_id``.

        Raises:
            ValueError: If neither or both scope identifiers are provided.
        """
        has_user = user_id is not None
        has_session = session_id is not None
        if has_user == has_session:
            raise ValueError(
                "Exactly one of user_id or session_id must be provided"
            )
        if user_id is not None:
            return CartItem.user_id == user_id  # type: ignore[return-value]
        return CartItem.session_id == session_id  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_items(
        self,
        session: AsyncSession,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[CartItem]:
        """Load all cart items scoped to a user or session.

        Eager-loads product translations (for resolved product names) and
        variant data (for size/color display).

        Args:
            session: Active async DB session.
            user_id: Scope to a registered user.
            session_id: Scope to an anonymous session.

        Returns:
            List of cart items ordered by ``added_at``.
        """
        scope = self._scope_filter(user_id, session_id)
        stmt = (
            select(CartItem)
            .where(scope)
            .options(
                selectinload(CartItem.product).selectinload(
                    Product.translations
                ),
                selectinload(CartItem.variant),
            )
            .order_by(CartItem.added_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_own_item(
        self,
        session: AsyncSession,
        item_id: UUID,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> CartItem | None:
        """Fetch a cart item by ID, scoped to user or session.

        Args:
            session: Active async DB session.
            item_id: The cart item UUID.
            user_id: Scope to a registered user.
            session_id: Scope to an anonymous session.

        Returns:
            The cart item or ``None`` if not found or not owned.
        """
        scope = self._scope_filter(user_id, session_id)
        stmt = select(CartItem).where(
            CartItem.id == item_id,
            scope,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_existing(
        self,
        session: AsyncSession,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        product_id: UUID,
        variant_id: UUID | None = None,
    ) -> CartItem | None:
        """Find an existing cart item matching scope + partial unique index.

        Uses the correct unique index depending on scope (user or session)
        and whether a variant is specified.

        Args:
            session: Active async DB session.
            user_id: Scope to a registered user.
            session_id: Scope to an anonymous session.
            product_id: The product UUID.
            variant_id: Optional variant UUID.

        Returns:
            The existing cart item or ``None``.
        """
        scope = self._scope_filter(user_id, session_id)
        if variant_id is not None:
            stmt = select(CartItem).where(
                scope,
                CartItem.variant_id == variant_id,
            )
        else:
            stmt = select(CartItem).where(
                scope,
                CartItem.product_id == product_id,
                CartItem.variant_id.is_(None),
            )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    async def upsert_item(
        self,
        session: AsyncSession,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        product_id: UUID,
        variant_id: UUID | None = None,
        qty: int,
        unit_price: Decimal,
    ) -> CartItem:
        """Add a cart item; increment quantity if already present.

        Checks for an existing item matching the scope + product/variant
        combination.  If found, increments quantity.  If not, inserts a new
        ``CartItem`` row.

        Args:
            session: Active async DB session.
            user_id: Scope to a registered user.
            session_id: Scope to an anonymous session.
            product_id: The product UUID.
            variant_id: Optional variant UUID.
            qty: Quantity to add.
            unit_price: Snapshotted unit price at add-time.

        Returns:
            The cart item (newly created or updated).
        """
        existing = await self.find_existing(
            session,
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            variant_id=variant_id,
        )

        if existing is not None:
            existing.quantity += qty
            await session.flush()
            return existing

        cart_item = CartItem(
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=qty,
            unit_price=unit_price,
        )
        session.add(cart_item)
        await session.flush()
        return cart_item

    async def update_qty(
        self,
        session: AsyncSession,
        item_id: UUID,
        qty: int,
    ) -> None:
        """Update the quantity of a cart item by ID.

        Setting quantity to 0 removes the item.

        Args:
            session: Active async DB session.
            item_id: The cart item UUID.
            qty: New quantity (0 to remove).
        """
        if qty == 0:
            await self._delete_by_id(session, item_id)
        else:
            await session.execute(
                update(CartItem)
                .where(CartItem.id == item_id)
                .values(quantity=qty)
            )
            await session.flush()

    async def remove_item(
        self,
        session: AsyncSession,
        item_id: UUID,
    ) -> None:
        """Delete a cart item by ID.

        Args:
            session: Active async DB session.
            item_id: The cart item UUID.
        """
        await self._delete_by_id(session, item_id)

    async def clear_scope(
        self,
        session: AsyncSession,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> None:
        """Delete all cart items for a given scope.

        Args:
            session: Active async DB session.
            user_id: Scope to a registered user.
            session_id: Scope to an anonymous session.
        """
        scope = self._scope_filter(user_id, session_id)
        await session.execute(delete(CartItem).where(scope))
        await session.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _delete_by_id(
        self,
        session: AsyncSession,
        item_id: UUID,
    ) -> None:
        """Delete a single cart item by primary key."""
        stmt = select(CartItem).where(CartItem.id == item_id)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        if item is not None:
            await session.delete(item)

    async def count_by_variant(
        self, session: AsyncSession, variant_id: UUID
    ) -> int:
        """Count cart items referencing a specific variant."""
        from sqlalchemy import func as sqlfunc
        result = await session.scalar(
            select(sqlfunc.count())
            .select_from(CartItem)
            .where(CartItem.variant_id == variant_id)
        )
        return result or 0
