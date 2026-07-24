import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.newsletter_subscriber import NewsletterSubscriber

logger = logging.getLogger(__name__)


class NewsletterService:
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
        result = await session.execute(
            select(NewsletterSubscriber).where(
                NewsletterSubscriber.email == email,
                NewsletterSubscriber.unsubscribed_at.isnot(None),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.unsubscribed_at = None
            existing.consent_ip = ip
            existing.consent_user_agent = user_agent
            await session.flush()
            return

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
        result = await session.execute(
            select(NewsletterSubscriber).where(
                NewsletterSubscriber.email == email,
                NewsletterSubscriber.unsubscribed_at.is_(None),
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.unsubscribed_at = datetime.now(timezone.utc)
            await session.flush()
            logger.info("Unsubscribed: %s", email)

    async def is_subscribed(self, session: AsyncSession, email: str) -> bool:
        """Check if an email is actively subscribed."""
        email = email.lower().strip()
        result = await session.execute(
            select(NewsletterSubscriber).where(
                NewsletterSubscriber.email == email,
                NewsletterSubscriber.unsubscribed_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None
