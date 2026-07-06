from litestar import Controller, post
from litestar.di import Provide
from litestar.exceptions import ValidationException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session as _async_session_fn
from app.schemas.newsletter import SubscribeRequest, SubscribeResponse
from app.services.newsletter_service import NewsletterService


async def provide_newsletter_service() -> NewsletterService:
    return NewsletterService()


async def provide_session() -> AsyncSession:
    async with _async_session_fn() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class NewsletterController(Controller):
    path = "/api/v1/newsletter"
    tags = ["newsletter"]
    dependencies = {
        "service": Provide(provide_newsletter_service, sync_to_thread=False),
        "session": Provide(provide_session, sync_to_thread=False),
    }

    @post("/subscribe", status_code=201)
    async def subscribe(
        self,
        data: SubscribeRequest,
        service: NewsletterService,
        session: AsyncSession,
    ) -> SubscribeResponse:
        try:
            await service.subscribe(session, data.email, data.lang)
        except ValueError as exc:
            raise ValidationException(detail=str(exc)) from exc
        return SubscribeResponse(message="subscribed")
