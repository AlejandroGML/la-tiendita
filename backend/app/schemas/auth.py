"""Pydantic v2 request/response schemas for auth endpoints."""

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    preferred_lang: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Payload for POST /auth/refresh."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Returned on successful login, register, and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    """Payload for POST /auth/forgot-password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Payload for POST /auth/reset-password."""

    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class AdminLoginResponse(BaseModel):
    """First step of admin login — TOTP required."""
    require_2fa: bool = True
    login_token: str
    user: UserResponse | None = None


class Verify2faRequest(BaseModel):
    """Payload for POST /auth/verify-2fa."""
    login_token: str
    code: str


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
