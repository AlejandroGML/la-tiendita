"""Tests for admin audit logging — AuditEvent, AuditService, and AuditHandler.

Covers:
- AuditEvent dataclass immutability
- AuditService.create_audit_log (mock repository)
- AuditHandler round-trip (real DB via session fixture)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.core.events import AuditAction, AuditEvent
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def actor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_event(actor_id) -> AuditEvent:
    return AuditEvent(
        actor_id=actor_id,
        action=AuditAction.PRODUCT_CREATE,
        entity_type="product",
        entity_id=str(uuid.uuid4()),
        details={"slug": "chaqueta-denim", "name": "Chaqueta Denim"},
        ip_address="192.168.1.100",
    )


@pytest.fixture
def mock_audit_repo():
    return AsyncMock(spec=AuditRepository)


@pytest.fixture
def mock_session():
    return AsyncMock()


# ---------------------------------------------------------------------------
# Unit: AuditEvent dataclass
# ---------------------------------------------------------------------------


class TestAuditEvent:
    """AuditEvent frozen dataclass — immutability and attribute access."""

    def test_is_frozen(self, sample_event):
        """AuditEvent must be immutable (frozen=True)."""
        with pytest.raises(Exception):
            sample_event.actor_id = uuid.uuid4()  # type: ignore[misc]

    def test_attribute_access(self, sample_event, actor_id):
        """All attributes are accessible on the frozen instance."""
        assert sample_event.actor_id == actor_id
        assert sample_event.action == AuditAction.PRODUCT_CREATE
        assert sample_event.entity_type == "product"
        assert isinstance(sample_event.entity_id, str)
        assert sample_event.details == {"slug": "chaqueta-denim", "name": "Chaqueta Denim"}
        assert sample_event.ip_address == "192.168.1.100"

    def test_defaults_are_none(self):
        """Optional fields default to None."""
        event = AuditEvent(
            actor_id=uuid.uuid4(),
            action=AuditAction.PRODUCT_DELETE,
            entity_type="product",
            entity_id=str(uuid.uuid4()),
        )
        assert event.details is None
        assert event.ip_address is None

    def test_action_enum_maps_to_string(self):
        """AuditAction enum values are the dot-notation strings."""
        assert AuditAction.PRODUCT_CREATE == "product.create"
        assert AuditAction.ORDER_STATUS_CHANGE == "order.status_change"
        assert AuditAction.USER_ROLE_CHANGE == "user.role_change"


# ---------------------------------------------------------------------------
# Unit: AuditService
# ---------------------------------------------------------------------------


class TestAuditService:
    """AuditService.create_audit_log — persists correct AuditLog via repo."""

    @pytest.mark.asyncio
    async def test_create_audit_log_calls_repo_add(
        self, mock_session, mock_audit_repo, sample_event
    ):
        """AuditService.create_audit_log should call repo.add with an AuditLog."""
        svc = AuditService(audit_repo=mock_audit_repo)

        result = await svc.create_audit_log(mock_session, sample_event)

        # Verify repo.add was called once
        mock_audit_repo.add.assert_awaited_once()
        call_args = mock_audit_repo.add.call_args
        audit_log = call_args[0][1]  # second positional arg (first is session)

        # Verify the AuditLog fields match the event
        assert isinstance(audit_log, AuditLog)
        assert audit_log.actor_id == sample_event.actor_id
        assert audit_log.action == AuditAction.PRODUCT_CREATE
        assert audit_log.entity_type == "product"
        assert audit_log.entity_id == sample_event.entity_id
        assert audit_log.details == {"slug": "chaqueta-denim", "name": "Chaqueta Denim"}
        assert audit_log.ip_address == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_returns_flushed_audit_log(
        self, mock_session, mock_audit_repo, sample_event
    ):
        """AuditService returns the AuditLog returned by repo.add."""
        svc = AuditService(audit_repo=mock_audit_repo)

        result = await svc.create_audit_log(mock_session, sample_event)
        assert result is mock_audit_repo.add.return_value


# ---------------------------------------------------------------------------
# Integration: AuditHandler round-trip
# ---------------------------------------------------------------------------

# The AuditHandler integration test requires a real PostgreSQL session.
# These tests depend on the ``session`` fixture from conftest.py and the
# ``test_user`` fixture below.


@pytest_asyncio.fixture
async def test_user(session):
    """Create a real user in the test DB for audit actor_id FK."""
    from app.models.user import User, UserRole

    user = User(
        email=f"audit-test-{uuid.uuid4().hex[:8]}@test.com",
        name="Audit Test Admin",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    session.add(user)
    await session.flush()
    return user


class TestAuditHandlerIntegration:
    """Integration: AuditHandler persists AuditLog after event emission."""

    @pytest.mark.asyncio
    async def test_handler_round_trip(self, session, test_user):
        """Emit AuditEvent → AuditHandler writes AuditLog row."""
        from app.core.event_bus import event_bus
        from app.core.handlers.audit_handler import AuditHandler
        from app.db.engine import async_session

        # Wire the handler for this test
        handler = AuditHandler(
            event_bus=event_bus, session_factory=async_session
        )

        event = AuditEvent(
            actor_id=test_user.id,
            action=AuditAction.PRODUCT_CREATE,
            entity_type="product",
            entity_id=str(uuid.uuid4()),
            details={"slug": "test-product"},
            ip_address="10.0.0.1",
        )

        # Emit via the event bus (fire-and-forget task)
        event_bus.emit(event)

        # Give the asyncio task a moment to execute
        import asyncio
        await asyncio.sleep(0.2)

        # We need a fresh query to see the inserted row.
        # The handler used async_session which is a different session.
        # Commit the handler's work (in production this is auto-committed
        # via the session context manager, but test needs explicit commit
        # since handler's session is separate).
        # Actually the handler uses `async with session_factory() as s` — the
        # context manager commits on exit.
        from sqlalchemy import select

        result = await session.execute(
            select(AuditLog).where(AuditLog.actor_id == test_user.id)
        )
        rows = result.scalars().all()

        assert len(rows) >= 1
        log = rows[0]
        assert log.action == AuditAction.PRODUCT_CREATE
        assert log.entity_type == "product"
        assert log.details == {"slug": "test-product"}
        assert log.ip_address == "10.0.0.1"

        # Cleanup: unsubscribe to avoid side effects on other tests
        event_bus._subscribers.pop(AuditEvent, None)

    @pytest.mark.asyncio
    async def test_event_bus_accepts_audit_events(self, test_user):
        """Verify the event_bus can accept AuditEvent without crashing."""
        from app.core.event_bus import event_bus

        # Emit without any handlers subscribed — must not raise
        event_bus.emit(
            AuditEvent(
                actor_id=test_user.id,
                action=AuditAction.ORDER_STATUS_CHANGE,
                entity_type="order",
                entity_id=str(uuid.uuid4()),
                details={"from": "pending", "to": "confirmed"},
                ip_address=None,
            )
        )
        # No assertion needed — if emit() doesn't raise, test passes
