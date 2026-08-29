"""Unit tests for NewsletterService — subscribe, unsubscribe, is_subscribed.

Uses a mocked NewsletterSubscriberRepository (no DB needed).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.newsletter_service import NewsletterService


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def svc(repo):
    return NewsletterService(repo=repo)


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_creates_new_subscriber(self, svc, repo, mock_session):
        """A brand-new email creates a NewsletterSubscriber and flushes."""
        repo.get_unsubscribed_by_email = AsyncMock(return_value=None)
        mock_session.add = AsyncMock()
        mock_session.flush = AsyncMock()

        await svc.subscribe(mock_session, "  NEW@Example.com  ")

        repo.get_unsubscribed_by_email.assert_awaited_once_with(
            mock_session, "new@example.com"
        )
        # Se creó un subscriber con el email normalizado
        added = mock_session.add.call_args[0][0]
        assert added.email == "new@example.com"
        assert added.lang == "es"
        mock_session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_subscribe_reactivates_previous_subscriber(self, svc, repo, mock_session):
        """A previously unsubscribed email gets re-activated (unsubscribed_at=None)."""
        sub = AsyncMock()
        sub.unsubscribed_at = datetime.now(timezone.utc)
        repo.get_unsubscribed_by_email = AsyncMock(return_value=sub)

        await svc.subscribe(mock_session, "old@example.com", ip="1.2.3.4", user_agent="UA")

        assert sub.unsubscribed_at is None
        assert sub.consent_ip == "1.2.3.4"
        assert sub.consent_user_agent == "UA"
        mock_session.flush.assert_awaited()
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_ignores_duplicate_on_integrity_error(self, svc, repo, mock_session):
        """If flush raises IntegrityError, it is swallowed and logged."""
        from sqlalchemy.exc import IntegrityError

        repo.get_unsubscribed_by_email = AsyncMock(return_value=None)
        mock_session.flush = AsyncMock(side_effect=IntegrityError("x", {}, Exception("dup")))
        mock_session.rollback = AsyncMock()

        # No debe lanzar
        await svc.subscribe(mock_session, "dup@example.com")


class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribe_sets_unsubscribed_at(self, svc, repo, mock_session):
        """An active subscriber gets unsubscribed_at set."""
        sub = AsyncMock()
        sub.unsubscribed_at = None
        repo.get_active_by_email = AsyncMock(return_value=sub)

        await svc.unsubscribe(mock_session, "user@example.com")

        assert sub.unsubscribed_at is not None
        mock_session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_unsubscribe_does_nothing_when_not_subscribed(self, svc, repo, mock_session):
        """Unsubscribing an unknown email is a no-op."""
        repo.get_active_by_email = AsyncMock(return_value=None)

        await svc.unsubscribe(mock_session, "ghost@example.com")

        mock_session.flush.assert_not_called()


class TestIsSubscribed:
    @pytest.mark.asyncio
    async def test_is_subscribed_true_when_active(self, svc, repo, mock_session):
        repo.get_active_by_email = AsyncMock(return_value=AsyncMock())

        assert await svc.is_subscribed(mock_session, "YES@Example.com") is True
        repo.get_active_by_email.assert_awaited_once_with(mock_session, "yes@example.com")

    @pytest.mark.asyncio
    async def test_is_subscribed_false_when_unknown(self, svc, repo, mock_session):
        repo.get_active_by_email = AsyncMock(return_value=None)

        assert await svc.is_subscribed(mock_session, "no@example.com") is False