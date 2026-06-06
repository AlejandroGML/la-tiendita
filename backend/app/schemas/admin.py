"""Pydantic v2 schemas for admin dashboard, user management, and order control."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardStatsResponse(BaseModel):
    """Aggregate counts for the admin dashboard stat cards."""

    total_products: int
    total_users: int
    total_orders: int
    total_revenue: float


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
