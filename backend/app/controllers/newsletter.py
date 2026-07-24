from datetime import datetime, timezone
from litestar import Controller, delete, get, post
from litestar.connection import ASGIConnection
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
        request: ASGIConnection,
    ) -> SubscribeResponse:
        try:
            ip = request.client.host if request.client else None
            ua = request.headers.get("user-agent")
            await service.subscribe(session, data.email, data.lang, ip=ip, user_agent=ua)
        except ValueError as exc:
            raise ValidationException(detail=str(exc)) from exc
        return SubscribeResponse(message="subscribed")

    @delete("/unsubscribe", status_code=200)
    async def unsubscribe(
        self,
        email: str,
        session: AsyncSession,
        service: NewsletterService,
    ) -> SubscribeResponse:
        """Unsubscribe an email from the newsletter."""
        await service.unsubscribe(session, email)
        return SubscribeResponse(message="unsubscribed")

    @get("/status", status_code=200)
    async def status(
        self,
        email: str,
        session: AsyncSession,
        service: NewsletterService,
    ) -> dict:
        """Check if an email is currently subscribed."""
        is_subscribed = await service.is_subscribed(session, email)
        return {"email": email, "subscribed": is_subscribed}
