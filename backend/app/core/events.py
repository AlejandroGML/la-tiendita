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
