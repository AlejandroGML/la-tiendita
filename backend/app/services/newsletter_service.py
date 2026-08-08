import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.newsletter_subscriber_repository import (
    NewsletterSubscriberRepository,
)

logger = logging.getLogger(__name__)


class NewsletterService:
    """Newsletter subscribe/unsubscribe business logic.

    Data access is delegated to :class:`NewsletterSubscriberRepository` —
    no raw SQLAlchemy queries in the service layer.
    """

    def __init__(
        self,
        repo: NewsletterSubscriberRepository | None = None,
    ) -> None:
        self._repo = repo or NewsletterSubscriberRepository()

    async def subscribe(
        self,
        session: AsyncSession,
        email: str,
        lang: str = "es",
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        email = email.lower().strip()
        # Check if previously unsubscribed — re-activate
        existing = await self._repo.get_unsubscribed_by_email(session, email)
        if existing:
            existing.unsubscribed_at = None
            existing.consent_ip = ip
            existing.consent_user_agent = user_agent
            await session.flush()
            return

        from app.models.newsletter_subscriber import NewsletterSubscriber

        subscriber = NewsletterSubscriber(
            email=email,
            lang=lang,
            consent_ip=ip,
            consent_user_agent=user_agent,
        )
        session.add(subscriber)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            logger.debug("Duplicate newsletter subscription ignored: %s", email)

    async def unsubscribe(self, session: AsyncSession, email: str) -> None:
        """Soft-unsubscribe by setting unsubscribed_at."""
        email = email.lower().strip()
        sub = await self._repo.get_active_by_email(session, email)
        if sub:
            sub.unsubscribed_at = datetime.now(timezone.utc)
            await session.flush()
            logger.info("Unsubscribed: %s", email)

    async def is_subscribed(self, session: AsyncSession, email: str) -> bool:
        """Check if an email is actively subscribed."""
        email = email.lower().strip()
        return await self._repo.get_active_by_email(session, email) is not None
