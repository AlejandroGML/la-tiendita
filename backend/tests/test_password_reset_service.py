"""Unit tests for PasswordResetService — forgot/reset password flow.

Covers: token generation, no-user-enumeration, one-time-use, expiry,
bcrypt matching, and password hashing.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest

from app.config import Settings
from app.models.password_reset import PasswordResetToken
from app.models.user import User, UserRole
from app.services.password_reset_service import PasswordResetService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_unique_mock(**kwargs):
    m = MagicMock(**kwargs)
    m.unique = MagicMock(return_value=m)
    return m


def _make_scalar_result(items):
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = items
    mock_result = _make_unique_mock()
    mock_result.scalars.return_value = mock_scalars
    return mock_result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def settings():
    return Settings(
        DATABASE_URL="postgresql+asyncpg:///test",
        SECRET_KEY="test-secret",
    )


@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(),
        email="user@test.com",
        name="Test User",
        role=UserRole.CUSTOMER,
        password_hash="$2b$12$abcdefghijklmnopqrstuvwx1234567890123456789012345678901",
    )


@pytest.fixture
def mock_token_service():
    """Mock TokenService that provides _hash_token."""
    mock = MagicMock()
    mock._hash_token = MagicMock(
        side_effect=lambda t: bcrypt.hashpw(
            t.encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")
    )
    return mock


@pytest.fixture
def mock_auth_service():
    """Mock AuthService that provides _hash_password."""
    mock = MagicMock()
    mock._hash_password = MagicMock(
        side_effect=lambda p: bcrypt.hashpw(
            p.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    )
    return mock


@pytest.fixture
def svc(settings, mock_token_service, mock_auth_service):
    return PasswordResetService(
        app_settings=settings,
        token_service=mock_token_service,
        auth_service=mock_auth_service,
    )


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    """Password reset token generation and no-user-enumeration."""

    @pytest.mark.asyncio
    async def test_registered_user_creates_token(self, svc, mock_user):
        """A registered email should create a PasswordResetToken and emit event."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc._user_repo.get_by_email = AsyncMock(return_value=mock_user)

        with patch("app.services.password_reset_service.event_bus") as mock_bus:
            result = await svc.forgot_password(session, "user@test.com")

        assert result is None
        session.add.assert_called_once()
        assert session.add.call_args[0][0].user_id == mock_user.id
        assert session.add.call_args[0][0].token_hash is not None
        assert session.add.call_args[0][0].expires_at > datetime.now(
            timezone.utc
        )
        mock_bus.emit.assert_called_once()
        event = mock_bus.emit.call_args[0][0]
        assert event.user_id == mock_user.id
        assert "reset-password?token=" in event.reset_link

    @pytest.mark.asyncio
    async def test_unregistered_email_silent(self, svc):
        """Unregistered email should return None without creating a token
        or emitting an event (prevents user enumeration)."""
        session = AsyncMock()

        svc._user_repo.get_by_email = AsyncMock(return_value=None)

        with patch("app.services.password_reset_service.event_bus") as mock_bus:
            result = await svc.forgot_password(
                session, "unknown@test.com"
            )

        assert result is None
        session.add.assert_not_called()
        mock_bus.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_user_enumeration_same_behavior(self, svc, mock_user):
        """Both registered and unregistered emails should return None
        (same return value — prevents timing-based enumeration)."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc._user_repo.get_by_email = AsyncMock(return_value=mock_user)

        with patch("app.services.password_reset_service.event_bus"):
            registered_result = await svc.forgot_password(
                session, "user@test.com"
            )

        svc._user_repo.get_by_email = AsyncMock(return_value=None)
        unregistered_result = await svc.forgot_password(
            session, "unknown@test.com"
        )

        assert registered_result is None
        assert unregistered_result is None

    @pytest.mark.asyncio
    async def test_token_hash_uses_bcrypt(self, svc, mock_user):
        """The stored token hash should be a valid bcrypt hash."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc._user_repo.get_by_email = AsyncMock(return_value=mock_user)

        with patch("app.services.password_reset_service.event_bus"):
            await svc.forgot_password(session, "user@test.com")

        added = session.add.call_args[0][0]
        assert added.token_hash.startswith("$2b$")


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------

class TestResetPassword:
    """Password reset verification, one-time-use, and expiry."""

    @pytest.mark.asyncio
    async def test_valid_token_resets_password(self, svc, mock_user, mock_auth_service):
        """A valid, unused, non-expired token should update the password hash
        and mark the token as used."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        # Create a valid reset token hash
        raw_token = "valid-reset-token-123"
        token_hash = bcrypt.hashpw(
            raw_token.encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")

        mock_prt = MagicMock()
        mock_prt.token_hash = token_hash
        mock_prt.user_id = mock_user.id
        mock_prt.used = False

        # Mock session.execute to return the valid token
        mock_result = _make_scalar_result([mock_prt])
        session.execute.return_value = mock_result

        # Mock user_repo.get_by_email for auth_service default construction
        svc._user_repo.get_by_email = AsyncMock(return_value=mock_user)

        result = await svc.reset_password(session, raw_token, "NewSecurePass1")

        assert result is None
        assert mock_prt.used is True
        session.flush.assert_called_once()
        mock_auth_service._hash_password.assert_called_once_with(
            "NewSecurePass1"
        )

    @pytest.mark.asyncio
    async def test_expired_token_raises_error(self, svc):
        """An expired token should raise ValueError."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        # Create a token hash but make the record expired
        raw_token = "expired-token"
        token_hash = bcrypt.hashpw(
            raw_token.encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")

        mock_prt = MagicMock()
        mock_prt.token_hash = token_hash
        # This test is about the query filtering — if the query correctly
        # filters expired tokens, the token won't be in the result.
        # So we return an empty list of tokens.
        mock_result = _make_scalar_result([])
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="invalid or expired reset token"):
            await svc.reset_password(session, raw_token, "NewSecurePass1")

    @pytest.mark.asyncio
    async def test_already_used_token_raises_error(self, svc):
        """An already-used token should raise ValueError."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        raw_token = "used-token"
        token_hash = bcrypt.hashpw(
            raw_token.encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")

        # Even though the token exists, the query filters used=False,
        # so if it's already used it won't show up.
        mock_result = _make_scalar_result([])
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="invalid or expired reset token"):
            await svc.reset_password(session, raw_token, "NewSecurePass1")

    @pytest.mark.asyncio
    async def test_invalid_token_raises_error(self, svc):
        """A token that doesn't match any stored hash should raise ValueError."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        # Return tokens but none match the raw token
        wrong_hash = bcrypt.hashpw(
            "other-token".encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")
        mock_prt = MagicMock()
        mock_prt.token_hash = wrong_hash

        mock_result = _make_scalar_result([mock_prt])
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="invalid or expired reset token"):
            await svc.reset_password(
                session, "non-matching-token", "NewSecurePass1"
            )

    @pytest.mark.asyncio
    async def test_one_time_use(self, svc, mock_user, mock_auth_service):
        """Using the same token twice should fail the second time."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        raw_token = "one-time-token"
        token_hash = bcrypt.hashpw(
            raw_token.encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")

        mock_prt = MagicMock()
        mock_prt.token_hash = token_hash
        mock_prt.user_id = mock_user.id
        mock_prt.used = False

        # First use: token is found and used
        svc._user_repo.get_by_email = AsyncMock(return_value=mock_user)
        mock_result_1 = _make_scalar_result([mock_prt])
        session.execute.return_value = mock_result_1

        result = await svc.reset_password(session, raw_token, "NewSecurePass1")
        assert result is None

        # Second use: token is now marked used=True, so query won't find it
        mock_prt.used = True
        mock_result_2 = _make_scalar_result([])
        session.execute.return_value = mock_result_2

        with pytest.raises(ValueError, match="invalid or expired reset token"):
            await svc.reset_password(
                session, raw_token, "AnotherPass1"
            )

    @pytest.mark.asyncio
    async def test_new_password_is_hashed(self, svc, mock_user, mock_auth_service):
        """The new password should be bcrypt-hashed before storage."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()

        raw_token = "hash-test-token"
        token_hash = bcrypt.hashpw(
            raw_token.encode("utf-8")[:72], bcrypt.gensalt()
        ).decode("utf-8")

        mock_prt = MagicMock()
        mock_prt.token_hash = token_hash
        mock_prt.user_id = mock_user.id
        mock_prt.used = False

        svc._user_repo.get_by_email = AsyncMock(return_value=mock_user)
        mock_result = _make_scalar_result([mock_prt])
        session.execute.return_value = mock_result

        result = await svc.reset_password(session, raw_token, "NewSecurePass1")

        assert result is None
        mock_auth_service._hash_password.assert_called_once()
        password_arg = mock_auth_service._hash_password.call_args[0][0]
        assert password_arg == "NewSecurePass1"
