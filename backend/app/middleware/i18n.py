"""i18n language detection ASGI middleware.

Detects the request language from:
1. ``?lang=`` query parameter (highest priority)
2. ``Accept-Language`` header (fallback)
3. Default ``"es"`` (fallback when neither is present or supported)

Sets ``request.state.lang`` (via ``scope["state"]["lang"]``) for downstream
handlers. Supported languages: ``es``, ``en``, ``sv``.
"""

from urllib.parse import parse_qs

from litestar.types import ASGIApp, Receive, Scope, Send

SUPPORTED_LANGS = {"es", "en", "sv"}
DEFAULT_LANG = "es"


def _extract_lang(scope: Scope) -> str:
    """Resolve the best language for the request."""
    # 1. Query parameter ?lang=
    query = parse_qs(scope.get("query_string", b"").decode())
    qp_lang: str | None = (
        query.get("lang", [None])[0]  # type: ignore[assignment]
    )
    if qp_lang is not None and qp_lang in SUPPORTED_LANGS:
        return qp_lang

    # 2. Accept-Language header
    headers = dict(scope.get("headers", []))
    accept_lang: str = headers.get(b"accept-language", b"").decode()
    if accept_lang:
        # Parse the first (highest priority) language tag
        primary = accept_lang.split(",")[0].strip().split(";")[0].strip()
        # Extract primary subtag (e.g., "es-MX" → "es")
        lang_code = primary.split("-")[0].lower()
        if lang_code in SUPPORTED_LANGS:
            return lang_code

    # 3. Default
    return DEFAULT_LANG


class I18nMiddleware:
    """Injects ``request.state.lang`` with the detected language."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "http":
            lang = _extract_lang(scope)
            scope.setdefault("state", {})["lang"] = lang  # type: ignore[index]

        await self.app(scope, receive, send)
