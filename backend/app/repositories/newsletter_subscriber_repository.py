"""NewsletterSubscriberRepository — data access for newsletter subscriptions."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.newsletter_subscriber import NewsletterSubscriber
from app.repositories.base import BaseRepository


class NewsletterSubscriberRepository(BaseRepository[NewsletterSubscriber]):
    """Newsletter-specific lookups — active vs previously unsubscribed."""

    def __init__(self) -> None:
        super().__init__(NewsletterSubscriber)

    async def get_unsubscribed_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> NewsletterSubscriber | None:
        """Find a previously unsubscribed subscriber by email (re-activation).

        Args:
            session: Active async DB session.
            email: The subscriber's email.

        Returns:
            The unsubscribed subscriber or ``None``.
        """
        return await self.find_one(
            session,
            NewsletterSubscriber.email == email,
            NewsletterSubscriber.unsubscribed_at.isnot(None),
        )

    async def get_active_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> NewsletterSubscriber | None:
        """Find an actively subscribed subscriber by email.

        Args:
            session: Active async DB session.
            email: The subscriber's email.

        Returns:
            The active subscriber or ``None``.
        """
        return await self.find_one(
            session,
            NewsletterSubscriber.email == email,
            NewsletterSubscriber.unsubscribed_at.is_(None),
        )
