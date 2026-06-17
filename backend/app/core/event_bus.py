"""In-memory pub/sub event bus with async fire-and-forget emission.

Typical usage::

    from app.core.event_bus import event_bus
    from app.core.events import WelcomeEmailEvent

    await event_bus.emit(WelcomeEmailEvent(user_id=user.id))
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

Handler = Callable[[Any], Coroutine[Any, Any, None]]
"""Signature for an event handler: ``async def handler(event: T) -> None``."""


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class EventBus:
    """Simple in-memory pub/sub event bus.

    * Subscribe handlers to typed events via :meth:`subscribe`.
    * Emit events via :meth:`emit` — handlers run as fire-and-forget
      ``asyncio.Task`` instances so the caller is never blocked.
    * Errors in individual handlers are logged and **never** propagated.
    """

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Handler]] = {}
        self._any_subscribers: list[Handler] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def subscribe(self, event_type: type, handler: Handler) -> None:
        """Register ``handler`` for a specific event type.

        Multiple handlers per type are supported.  Handlers are called in
        registration order.
        """
        self._subscribers.setdefault(event_type, []).append(handler)
        logger.debug(
            "Handler %s subscribed to %s",
            handler.__name__,
            event_type.__name__,
        )

    def subscribe_all(self, handler: Handler) -> None:
        """Register ``handler`` for **every** event type."""
        self._any_subscribers.append(handler)
        logger.debug("Handler %s subscribed to ALL events", handler.__name__)

    # ------------------------------------------------------------------
    # Emission  (fire-and-forget)
    # ------------------------------------------------------------------

    def emit(self, event: Any) -> None:
        """Schedule all handlers registered for ``type(event)``.

        Each handler runs as a separate ``asyncio.Task`` so emit() returns
        immediately.  Exceptions are caught and logged — callers are never
        affected by handler failures.
        """
        event_type = type(event)
        handlers = self._subscribers.get(event_type, []) + self._any_subscribers

        if not handlers:
            logger.debug("No handlers for event %s", event_type.__name__)
            return

        for handler in handlers:
            asyncio.create_task(
                self._invoke_safe(handler, event),
                name=f"{handler.__name__}-{event_type.__name__}",
            )

        logger.debug("Emitted %s to %d handler(s)", event_type.__name__, len(handlers))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    async def _invoke_safe(handler: Handler, event: Any) -> None:
        """Call ``handler(event)`` and log (but swallow) any exception."""
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Handler %s failed for event %s",
                handler.__name__,
                type(event).__name__,
            )


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

event_bus = EventBus()
"""Global ``EventBus`` instance for the application.

Import this wherever you need to emit or subscribe to events::

    from app.core.event_bus import event_bus
"""
