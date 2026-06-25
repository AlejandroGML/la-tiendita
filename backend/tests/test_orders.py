"""Unit tests for AdminOrderService — order state-machine guard clauses.

Validates ALLOWED_TRANSITIONS (invalid paths), TOCTOU detection,
and input validation. No PostgreSQL or Litestar needed.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.order import OrderStatus, PaymentStatus
from app.services.admin_order_service import (
    AdminOrderService,
    InvalidTransitionError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_order(
    *,
    order_id: uuid.UUID | None = None,
    status: OrderStatus = OrderStatus.PENDING,
    payment_status: PaymentStatus = PaymentStatus.PAID,
    total: Decimal | None = None,
    user_name: str = "Test User",
) -> MagicMock:
    """Build a mock Order with the minimum attributes needed by
    AdminOrderService.update_order_status()."""
    order = MagicMock()
    order.id = order_id or uuid.uuid4()
    order.status = status
    order.payment_status = payment_status
    order.stripe_session_id = None
    order.total = total or Decimal("150.00")
    order.user = MagicMock()
    order.user.name = user_name
    order.created_at = datetime.now(timezone.utc)
    return order


# ---------------------------------------------------------------------------
# Invalid transitions — parametrized (all 15)
# ---------------------------------------------------------------------------

# Every pair of (current, target) where target is NOT in
# ALLOWED_TRANSITIONS[current]
INVALID_TRANSITIONS = [
    # From PENDING
    (OrderStatus.PENDING, OrderStatus.SHIPPED),
    (OrderStatus.PENDING, OrderStatus.DELIVERED),
    # From CONFIRMED
    (OrderStatus.CONFIRMED, OrderStatus.PENDING),
    (OrderStatus.CONFIRMED, OrderStatus.DELIVERED),
    # From SHIPPED
    (OrderStatus.SHIPPED, OrderStatus.PENDING),
    (OrderStatus.SHIPPED, OrderStatus.CONFIRMED),
    (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
    # From DELIVERED (terminal)
    (OrderStatus.DELIVERED, OrderStatus.PENDING),
    (OrderStatus.DELIVERED, OrderStatus.CONFIRMED),
    (OrderStatus.DELIVERED, OrderStatus.SHIPPED),
    (OrderStatus.DELIVERED, OrderStatus.CANCELLED),
    # From CANCELLED (terminal)
    (OrderStatus.CANCELLED, OrderStatus.PENDING),
    (OrderStatus.CANCELLED, OrderStatus.CONFIRMED),
    (OrderStatus.CANCELLED, OrderStatus.SHIPPED),
    (OrderStatus.CANCELLED, OrderStatus.DELIVERED),
]


class TestInvalidTransitions:
    """Every disallowed transition raises InvalidTransitionError."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("current,target", INVALID_TRANSITIONS)
    async def test_invalid_transition_raises(self, svc, session, current, target):
        """Invalid transition raises InvalidTransitionError before DB write."""
        order = _make_order(status=current)
        session.scalar = AsyncMock(return_value=order)
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        with pytest.raises(InvalidTransitionError) as exc_info:
            await svc.update_order_status(
                session, order.id, target.value
            )

        error_msg = str(exc_info.value)
        assert "cannot transition" in error_msg
        assert current.value in error_msg
        assert target.value in error_msg

        # DB write must NOT have been attempted
        session.execute.assert_not_called()
        session.flush.assert_not_called()


# ---------------------------------------------------------------------------
# TOCTOU race
# ---------------------------------------------------------------------------


class TestTOCTOURace:
    """Concurrent admin updates must detect lost races."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_toctou_race_detected(self, svc, session):
        """When atomic UPDATE returns rowcount=0, an InvalidTransitionError is raised."""
        order = _make_order(status=OrderStatus.PENDING)
        session.scalar = AsyncMock(return_value=order)

        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)
        session.flush = AsyncMock()

        with pytest.raises(InvalidTransitionError) as exc_info:
            await svc.update_order_status(
                session, order.id, OrderStatus.CONFIRMED.value
            )

        assert "has already been transitioned" in str(exc_info.value)
        session.execute.assert_called_once()
        # flush must NOT be called after a zero-rowcount update
        session.flush.assert_not_called()


# ---------------------------------------------------------------------------
# Invalid status string
# ---------------------------------------------------------------------------


class TestInvalidStatusString:
    """Passing a non-existent status string must raise ValueError."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_bogus_status_raises_value_error(self, svc, session):
        """Passing 'bogus' as the target status raises ValueError."""
        order = _make_order(status=OrderStatus.PENDING)
        session.scalar = AsyncMock(return_value=order)

        with pytest.raises(ValueError) as exc_info:
            await svc.update_order_status(session, order.id, "bogus")

        assert "invalid status" in str(exc_info.value)
        assert "bogus" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Order not found
# ---------------------------------------------------------------------------


class TestOrderNotFound:
    """Non-existent order IDs must raise ValueError."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_order_not_found(self, svc, session):
        """When scalar returns None, a ValueError is raised."""
        session.scalar = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await svc.update_order_status(
                session, uuid.uuid4(), OrderStatus.CONFIRMED.value
            )

        assert "not found" in str(exc_info.value)
