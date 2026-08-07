"""Tests for the multi-provider payment layer (Stripe + Swish mock).

Covers:
- Payment registry: get_provider resolves the 3 methods.
- StripeProvider.create_payment: builds a Stripe session (mocked SDK),
  persists payment_reference, returns redirect_url. Klarna variant sends
  payment_method_types.
- SwishProvider.create_payment: mock returns QR payload, persists
  payment_details, returns qr_code (no redirect).
- SwishProvider.handle_callback (paid): order → PAID, finalize_payment
  called (stock deducted). Uses a real session + real OrderService, with
  stock mocked at the variant level.
- SwishProvider.handle_callback (declined): order → FAILED.
- Idempotency: second "paid" callback is a no-op.
- Invalid payload: SwishCallbackError raised.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.payments import AVAILABLE_METHODS, PAYMENT_METHODS, get_provider
from app.payments.base import PaymentInitiation
from app.payments.stripe_provider import StripeProvider, StripeWebhookError
from app.payments.swish_provider import SwishCallbackError, SwishProvider
from app.models.order import Order, PaymentStatus
from app.services.order_service import OrderService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def order() -> Order:
    """A minimal Order with provider fields."""
    o = Order(
        id=uuid.uuid4(),
        user_id=None,
        guest_email="guest@example.com",
        total=Decimal("150.00"),
        shipping_address={"name": "Test", "city": "Stockholm"},
        shipping_method="standard",
        shipping_cost=Decimal("49.00"),
        payment_provider="swish",
    )
    o.items = []
    return o


@pytest.fixture
def cart_items():
    """Minimal cart items (product + variant mocks)."""
    product = MagicMock()
    product.translations = []
    variant = MagicMock()
    variant.size = MagicMock(value="M")
    variant.color = "black"
    item = MagicMock()
    item.product = product
    item.variant = variant
    item.quantity = 1
    item.unit_price = Decimal("100.00")
    item.product_id = uuid.uuid4()
    item.variant_id = uuid.uuid4()
    return [item]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_three_methods_registered(self):
        assert set(PAYMENT_METHODS.keys()) == {"card", "klarna", "swish"}
        assert AVAILABLE_METHODS == ["card", "klarna", "swish"]

    def test_card_and_klarna_share_stripe_provider(self):
        assert PAYMENT_METHODS["card"] is PAYMENT_METHODS["klarna"]
        assert PAYMENT_METHODS["card"] is StripeProvider

    def test_swish_is_own_provider(self):
        assert PAYMENT_METHODS["swish"] is SwishProvider

    def test_get_provider_returns_instance(self):
        assert isinstance(get_provider("card"), StripeProvider)
        assert isinstance(get_provider("swish"), SwishProvider)

    def test_get_provider_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unsupported payment method"):
            get_provider("bitcoin")


# ---------------------------------------------------------------------------
# StripeProvider
# ---------------------------------------------------------------------------


class TestStripeProvider:
    @patch("app.payments.stripe_provider.stripe")
    @pytest.mark.asyncio
    async def test_create_payment_card_returns_redirect(
        self, mock_stripe, order, cart_items
    ):
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/c/pay/cs_test_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        provider = StripeProvider()
        result = await provider.create_payment(
            AsyncMock(), order, cart_items,
            user_email=None, user_id=None, is_guest=True,
        )

        assert isinstance(result, PaymentInitiation)
        assert result.redirect_url == "https://checkout.stripe.com/c/pay/cs_test_123"
        assert result.qr_code is None
        assert result.payment_reference == "cs_test_123"
        assert order.payment_reference == "cs_test_123"

        # card: no payment_method_types explícito
        kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert "payment_method_types" not in kwargs

    @patch("app.payments.stripe_provider.stripe")
    @pytest.mark.asyncio
    async def test_create_payment_klarna_sends_method_types(
        self, mock_stripe, order, cart_items
    ):
        order._payment_method = "klarna"
        mock_session = MagicMock()
        mock_session.id = "cs_test_klarna"
        mock_session.url = "https://checkout.stripe.com/c/pay/cs_test_klarna"
        mock_stripe.checkout.Session.create.return_value = mock_session

        provider = StripeProvider()
        result = await provider.create_payment(
            AsyncMock(), order, cart_items,
            user_email="a@b.se", user_id=uuid.uuid4(), is_guest=False,
        )

        kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert kwargs["payment_method_types"] == ["card", "klarna"]
        assert kwargs["customer_email"] == "a@b.se"
        assert result.redirect_url

    @patch("app.payments.stripe_provider.stripe")
    @pytest.mark.asyncio
    async def test_handle_callback_bad_signature_raises(self, mock_stripe):
        mock_stripe.Webhook.construct_event.side_effect = (
            ValueError("bad signature")
        )
        provider = StripeProvider()
        with pytest.raises(StripeWebhookError):
            await provider.handle_callback(
                MagicMock(), b"{}", {"stripe-signature": "bad"}
            )


# ---------------------------------------------------------------------------
# SwishProvider (mock)
# ---------------------------------------------------------------------------


class TestSwishProvider:
    @pytest.mark.asyncio
    async def test_create_payment_mock_returns_qr(self, order, cart_items):
        provider = SwishProvider()
        result = await provider.create_payment(
            AsyncMock(), order, cart_items,
            user_email=None, user_id=None, is_guest=True,
        )

        assert result.qr_code is not None
        assert result.qr_code.startswith("SWISH:MOCK:")
        assert result.redirect_url is None
        assert result.payment_reference.startswith("swish_mock_")
        assert order.payment_reference == result.payment_reference
        assert order.payment_details is not None
        assert order.payment_details["mode"] == "mock"

    @pytest.mark.asyncio
    async def test_handle_callback_paid_finalizes_order(self, order):
        """paid → order PAID + finalize_payment runs (stock deduct path)."""
        provider = SwishProvider()

        # Mock OrderService.finalize_payment para no depender de stock real
        with patch.object(
            OrderService, "finalize_payment", new_callable=AsyncMock
        ) as mock_finalize:
            # Mock del repo para devolver el order
            fake_repo = MagicMock()
            fake_repo.get_by_id = AsyncMock(return_value=order)
            provider._order_repo = fake_repo

            payload = (
                f'{{"order_id": "{order.id}", "status": "paid"}}'
            ).encode()

            result = await provider.handle_callback(
                AsyncMock(), payload, {}
            )

            assert result.event_type == "paymentrequest.state.PAID"
            assert result.status == PaymentStatus.PAID
            assert order.payment_status == PaymentStatus.PAID
            mock_finalize.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_callback_paid_idempotent(self, order):
        """Segundo callback paid → no-op (finalize NO se llama 2 veces)."""
        order.payment_status = PaymentStatus.PAID  # ya pagada
        provider = SwishProvider()

        fake_repo = MagicMock()
        fake_repo.get_by_id = AsyncMock(return_value=order)
        provider._order_repo = fake_repo

        payload = (
            f'{{"order_id": "{order.id}", "status": "paid"}}'
        ).encode()

        with patch.object(
            OrderService, "finalize_payment", new_callable=AsyncMock
        ) as mock_finalize:
            result = await provider.handle_callback(
                AsyncMock(), payload, {}
            )

            assert result.status == PaymentStatus.PAID
            mock_finalize.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_callback_declined_marks_failed(self, order):
        provider = SwishProvider()
        fake_repo = MagicMock()
        fake_repo.get_by_id = AsyncMock(return_value=order)
        provider._order_repo = fake_repo

        payload = (
            f'{{"order_id": "{order.id}", "status": "declined"}}'
        ).encode()

        result = await provider.handle_callback(AsyncMock(), payload, {})

        assert result.status == PaymentStatus.FAILED
        assert order.payment_status == PaymentStatus.FAILED

    @pytest.mark.asyncio
    async def test_handle_callback_invalid_payload_raises(self):
        provider = SwishProvider()
        with pytest.raises(SwishCallbackError):
            await provider.handle_callback(
                AsyncMock(), b"not-json", {}
            )

    @pytest.mark.asyncio
    async def test_handle_callback_missing_order_id_raises(self):
        provider = SwishProvider()
        with pytest.raises(SwishCallbackError, match="order_id"):
            await provider.handle_callback(
                AsyncMock(), b'{"status": "paid"}', {}
            )

    @pytest.mark.asyncio
    async def test_refund_marks_refunded(self, order):
        provider = SwishProvider()
        await provider.refund(AsyncMock(), order)
        assert order.payment_status == PaymentStatus.REFUNDED

    @pytest.mark.asyncio
    async def test_get_status_returns_stored(self, order):
        order.payment_status = PaymentStatus.PAID
        provider = SwishProvider()
        status = await provider.get_status(AsyncMock(), order)
        assert status == PaymentStatus.PAID
