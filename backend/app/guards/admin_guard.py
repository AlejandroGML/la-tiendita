"""Admin guard — rejects requests where ``request.user.role != "admin"``.

Must be applied AFTER ``jwt_auth`` so that ``request.user`` is already populated.
Returns 403 Forbidden for non-admin users.
"""

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler


def admin_guard(
    connection: ASGIConnection, route_handler: BaseRouteHandler
) -> None:
    """Litestar before-request guard. Checks ``request.user.role == "admin"``."""
    user = getattr(connection, "user", None)
    if user is None or getattr(user, "role", None) != "admin":
        raise NotAuthorizedException(detail="admin access required")
