"""Pydantic v2 schemas for admin dashboard, user management, and order control."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardStatsResponse(BaseModel):
    """Aggregate counters for the admin dashboard stat cards.

    All fields are non-negative. ``reviews_avg_rating`` is 0.0–5.0.
    New fields are optional with defaults for backward compatibility
    with existing clients.
    """

    total_products: int
    total_users: int
    total_orders: int
    total_revenue: float

    # Order status breakdown
    orders_pending: int = 0
    orders_confirmed: int = 0
    orders_shipped: int = 0
    orders_delivered: int = 0

    # Review health
    reviews_total: int = 0
    reviews_avg_rating: float = 0.0

    # Marketing
    promotions_active: int = 0

    # Current-month aggregates
    revenue_month: float = 0.0
    orders_month: int = 0


class UserAdminItem(BaseModel):
    """A user row as seen by an admin — includes orders_count for context."""

    id: UUID
    email: str
    name: str
    role: str
    is_verified: bool
    orders_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    """Payload for PATCH /api/admin/users/{id}/role — change a user's role."""

    role: str


class OrderStatusUpdate(BaseModel):
    """Payload for PATCH /api/admin/orders/{id}/status — transition order state."""

    status: str
