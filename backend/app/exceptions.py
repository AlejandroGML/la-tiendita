"""Shared exception classes for the application.

Moved here from individual service modules to break circular imports:
- ``StripeError`` was defined in ``stripe_service.py``
- ``StockInsufficientError`` was defined in ``order_service.py``
"""


class StripeError(RuntimeError):
    """Raised when a Stripe API call fails."""


class StockInsufficientError(ValueError):
    """Raised when one or more cart items exceed available stock."""
