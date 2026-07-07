"""ShippingController — available shipping methods with costs."""

from dataclasses import dataclass

from litestar import Controller, get


@dataclass
class ShippingMethod:
    """A shipping option available at checkout."""

    id: str
    name: str
    price: float
    estimated_days: str


# ── Available methods (config-backed in future) ──────────────────────
# These are hardcoded for MVP.  Could be moved to DB or Stripe shipping
# rates when the business model is validated.

_SHIPPING_METHODS: list[ShippingMethod] = [
    ShippingMethod(
        id="standard",
        name="Envío Estándar",
        price=49.0,
        estimated_days="5-7 días hábiles",
    ),
    ShippingMethod(
        id="express",
        name="Envío Express",
        price=99.0,
        estimated_days="1-2 días hábiles",
    ),
    ShippingMethod(
        id="pickup",
        name="Retiro en Tienda",
        price=0.0,
        estimated_days="—",
    ),
]


class ShippingController(Controller):
    """Shipping methods — public, no auth required."""

    path = "/api/v1/shipping"
    tags = ["shipping"]

    @get("/methods")
    async def list_methods(self) -> list[dict]:
        """Return available shipping methods with prices."""
        return [
            {
                "id": m.id,
                "name": m.name,
                "price": m.price,
                "estimated_days": m.estimated_days,
            }
            for m in _SHIPPING_METHODS
        ]
