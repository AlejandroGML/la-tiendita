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
    marketing_consent: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Optional fields a user can update on their own profile."""

    name: str | None = None
    phone: str | None = None
    preferred_lang: str | None = None


class UserAdminUpdate(BaseModel):
    """Fields an admin can modify on any user account."""

    name: str | None = None
    email: str | None = None
    role: str | None = None
    is_verified: bool | None = None
    marketing_consent: bool | None = None


class Setup2faResponse(BaseModel):
    """Response for 2FA setup — returns the secret and a provisioning URI."""
    secret: str
    uri: str
    qr_code_url: str


class Enable2faRequest(BaseModel):
    """Verify a TOTP code to enable 2FA."""
    code: str
