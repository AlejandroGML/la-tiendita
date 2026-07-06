import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.newsletter_subscriber import NewsletterSubscriber

logger = logging.getLogger(__name__)


class NewsletterService:
    async def subscribe(self, session: AsyncSession, email: str, lang: str = "es") -> None:
        subscriber = NewsletterSubscriber(email=email.lower().strip(), lang=lang)
        session.add(subscriber)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            logger.debug("Duplicate newsletter subscription ignored: %s", email)
