"""Unit tests for AdminOrderService — order state machine transitions.

Validates ALLOWED_TRANSITIONS via MockAsyncSession + AsyncMock,
exercising every valid transition, every invalid transition, TOCTOU
races, and invalid status strings. No PostgreSQL or Litestar needed.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.order import OrderStatus
from app.services.admin_order_service import (
    AdminOrderService,
    InvalidTransitionError,
)
from tests.conftest import MockAsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_order(
    *,
    order_id: uuid.UUID | None = None,
    status: OrderStatus = OrderStatus.PENDING,
    total: Decimal | None = None,
    user_name: str = "Test User",
) -> MagicMock:
    """Build a mock Order with the minimum attributes needed by
    AdminOrderService.update_order_status()."""
    order = MagicMock()
    order.id = order_id or uuid.uuid4()
    order.status = status
    order.total = total or Decimal("150.00")
    order.user = MagicMock()
    order.user.name = user_name
    order.created_at = datetime.now(timezone.utc)
    return order


# ---------------------------------------------------------------------------
# Valid transitions — parametrized
# ---------------------------------------------------------------------------

VALID_TRANSITIONS = [
    (OrderStatus.PENDING, OrderStatus.CONFIRMED),
    (OrderStatus.PENDING, OrderStatus.CANCELLED),
    (OrderStatus.CONFIRMED, OrderStatus.SHIPPED),
    (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
    (OrderStatus.SHIPPED, OrderStatus.DELIVERED),
]


class TestValidTransitions:
    """Every allowed transition returns an OrderAdminListItem."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def mock_session(self):
        return MockAsyncSession()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
    async def test_valid_transition(self, svc, mock_session, current, target):
        """Valid transition returns OrderAdminListItem with updated status."""
        order = _make_order(status=current)

        # Mock the reload (second scalar call returns the updated order)
        reloaded = _make_order(order_id=order.id, status=target)

        mock_session.scalar = AsyncMock(side_effect=[order, reloaded])

        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await svc.update_order_status(
            mock_session, order.id, target.value
        )

        assert result.status == target.value
        assert result.id == order.id
        assert result.user_name == order.user.name

        # Verify the atomic UPDATE was called
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()


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
    def mock_session(self):
        return MockAsyncSession()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("current,target", INVALID_TRANSITIONS)
    async def test_invalid_transition_raises(self, svc, mock_session, current, target):
        """Invalid transition raises InvalidTransitionError before DB write."""
        order = _make_order(status=current)
        mock_session.scalar = AsyncMock(return_value=order)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        with pytest.raises(InvalidTransitionError) as exc_info:
            await svc.update_order_status(
                mock_session, order.id, target.value
            )

        error_msg = str(exc_info.value)
        assert "cannot transition" in error_msg
        assert current.value in error_msg
        assert target.value in error_msg

        # DB write must NOT have been attempted
        mock_session.execute.assert_not_called()
        mock_session.flush.assert_not_called()


# ---------------------------------------------------------------------------
# TOCTOU race
# ---------------------------------------------------------------------------


class TestTOCTOURace:
    """Concurrent admin updates must detect lost races."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def mock_session(self):
        return MockAsyncSession()

    @pytest.mark.asyncio
    async def test_toctou_race_detected(self, svc, mock_session):
        """When atomic UPDATE returns rowcount=0, an InvalidTransitionError is raised."""
        order = _make_order(status=OrderStatus.PENDING)
        mock_session.scalar = AsyncMock(return_value=order)

        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        with pytest.raises(InvalidTransitionError) as exc_info:
            await svc.update_order_status(
                mock_session, order.id, OrderStatus.CONFIRMED.value
            )

        assert "has already been transitioned" in str(exc_info.value)
        mock_session.execute.assert_called_once()
        # flush must NOT be called after a zero-rowcount update
        mock_session.flush.assert_not_called()


# ---------------------------------------------------------------------------
# Invalid status string
# ---------------------------------------------------------------------------


class TestInvalidStatusString:
    """Passing a non-existent status string must raise ValueError."""

    @pytest.fixture
    def svc(self):
        return AdminOrderService()

    @pytest.fixture
    def mock_session(self):
        return MockAsyncSession()

    @pytest.mark.asyncio
    async def test_bogus_status_raises_value_error(self, svc, mock_session):
        """Passing 'bogus' as the target status raises ValueError."""
        order = _make_order(status=OrderStatus.PENDING)
        mock_session.scalar = AsyncMock(return_value=order)

        with pytest.raises(ValueError) as exc_info:
            await svc.update_order_status(mock_session, order.id, "bogus")

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
    def mock_session(self):
        return MockAsyncSession()

    @pytest.mark.asyncio
    async def test_order_not_found(self, svc, mock_session):
        """When scalar returns None, a ValueError is raised."""
        mock_session.scalar = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await svc.update_order_status(
                mock_session, uuid.uuid4(), OrderStatus.CONFIRMED.value
            )

        assert "not found" in str(exc_info.value)
