"""Pydantic v2 response/update schemas for the User resource."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Public user profile returned in API responses (never includes password)."""

    id: UUID
    email: str
    name: str
    role: str
    preferred_lang: str
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Optional fields a user can update on their own profile."""

    name: str | None = None
    phone: str | None = None
    preferred_lang: str | None = None
