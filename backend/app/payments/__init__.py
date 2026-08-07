"""Payment method registry — maps frontend method names to providers.

A single provider can serve multiple methods (Stripe serves both
"card" and "klarna" via its Checkout API).
"""

from __future__ import annotations

from app.payments.base import PaymentProvider
from app.payments.stripe_provider import StripeProvider
from app.payments.swish_provider import SwishProvider

#: method -> provider class
PAYMENT_METHODS: dict[str, type[PaymentProvider]] = {
    "card": StripeProvider,    # tarjeta vía Stripe hosted checkout
    "klarna": StripeProvider,  # Klarna vía Stripe (payment_method_types)
    "swish": SwishProvider,    # Swish directo (mock en local)
}

#: Métodos que puede ofrecer cada provider (para el frontend)
AVAILABLE_METHODS: list[str] = list(PAYMENT_METHODS.keys())


def get_provider(method: str) -> PaymentProvider:
    """Return a provider instance for the given payment method.

    Raises:
        ValueError: if the method is not registered.
    """
    provider_cls = PAYMENT_METHODS.get(method)
    if provider_cls is None:
        raise ValueError(
            f"Unsupported payment method: {method!r}. "
            f"Available: {', '.join(AVAILABLE_METHODS)}"
        )
    return provider_cls()
