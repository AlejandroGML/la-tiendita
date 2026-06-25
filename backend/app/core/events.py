"""Typed event dataclasses for the application event bus.

Each datacarry the **minimum** data required for its handler to do its job.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class WelcomeEmailEvent:
    """Emitted after a new user successfully registers.

    Attributes:
        user_id: The newly created user's UUID.
    """

    user_id: UUID


@dataclass(frozen=True)
class OrderConfirmationEvent:
    """Emitted after an order is paid and confirmed.

    Attributes:
        user_id:  The ordering user's UUID.
        order_id: The confirmed order's UUID.
    """

    user_id: UUID
    order_id: UUID


@dataclass(frozen=True)
class PasswordResetEvent:
    """Emitted when a user requests a password reset.

    Attributes:
        user_id:   The user requesting the reset.
        reset_link: Full URL with the one-time token.
    """

    user_id: UUID
    reset_link: str


@dataclass(frozen=True)
class OrderShippedEvent:
    """Emitted when an admin transitions an order to ``shipped``.

    Attributes:
        user_id:  The ordering user's UUID.
        order_id: The order whose status changed to Shipped.
    """

    user_id: UUID
    order_id: UUID


@dataclass(frozen=True)
class ProductChangedEvent:
    """Emitted after a product is created, updated, or soft-deleted.

    Drives cache invalidation of product listing/detail keys. ``action`` uses
    past tense (``created``/``updated``/``deleted``).

    Attributes:
        product_id: The product's UUID.
        action:     Past-tense mutation verb.
        slug:       The product slug, used to target its detail cache key.
                    ``None`` for creates (no detail key exists yet).
    """

    product_id: UUID
    action: str
    slug: str | None = None


@dataclass(frozen=True)
class CategoryChangedEvent:
    """Emitted after a category create/update/delete to invalidate its cache.

    Attributes:
        category_id: The category's integer ID.
        action:      Past-tense mutation verb.
    """

    category_id: int
    action: str


@dataclass(frozen=True)
class PromotionChangedEvent:
    """Emitted after a promotion mutation.

    Because promotions are baked into cached product pricing, this event
    triggers cross-entity invalidation (promotions + all product keys).

    Attributes:
        promotion_id: The promotion's UUID.
        action:       Past-tense mutation verb.
    """

    promotion_id: UUID
    action: str
