"""Unit tests for TokenService — JWT creation/verification, refresh rotation,
logout, bcrypt hashing, and user-ID extraction."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import pytest

from app.config import Settings
from app.models.user import User, UserRole
from app.schemas.auth import RefreshRequest
from app.services.token_service import TokenService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_unique_mock(**kwargs):
    """Build a mock that supports ``.unique()`` returning itself."""
    m = MagicMock(**kwargs)
    m.unique = MagicMock(return_value=m)
    return m


def _make_scalar_result(items):
    """Build a mock that supports ``.scalars().all()`` returning a list."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = items
    mock_result = _make_unique_mock()
    mock_result.scalars.return_value = mock_scalars
    return mock_result


# ---------------------------------------------------------------------------
# JWT Access Token Create / Verify
# ---------------------------------------------------------------------------

class TestAccessToken:
    """JWT access token creation and verification."""

    @pytest.fixture
    def svc(self):
        return TokenService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret-key-for-unit-tests",
                ACCESS_TOKEN_EXPIRE_MINUTES=15,
                JWT_ALGORITHM="HS256",
            )
        )

    def test_create_access_token_contains_claims(self, svc):
        token = svc.create_access_token_raw("user-1", "customer")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self, svc):
        token = svc.create_access_token_raw("user-1", "customer")
        claims = svc.verify_access_token(token)
        assert claims is not None
        assert claims["sub"] == "user-1"
        assert claims["role"] == "customer"
        assert "exp" in claims
        assert "iat" in claims

    def test_verify_tampered_token_fails(self, svc):
        token = svc.create_access_token_raw("user-1", "customer")
        tampered = token + "x"
        claims = svc.verify_access_token(tampered)
        assert claims is None

    def test_verify_expired_token_fails(self, svc):
        svc_expired = TokenService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
                ACCESS_TOKEN_EXPIRE_MINUTES=-1,
                JWT_ALGORITHM="HS256",
            )
        )
        token = svc_expired.create_access_token_raw("user-1", "customer")
        claims = svc.verify_access_token(token)
        assert claims is None

    def test_different_role_in_claim(self, svc):
        token = svc.create_access_token_raw("user-2", "admin")
        claims = svc.verify_access_token(token)
        assert claims is not None
        assert claims["role"] == "admin"

    def test_create_login_token_has_purpose(self, svc):
        token = svc.create_login_token("user-1")
        claims = svc.verify_access_token(token)
        assert claims is not None
        assert claims["purpose"] == "2fa_login"
        assert claims["sub"] == "user-1"

    def test_create_login_token_short_expiry(self, svc):
        """Login token expires in ~5 minutes (short-lived)."""
        token = svc.create_login_token("user-1")
        claims = svc.verify_access_token(token)
        assert claims is not None
        # exp - iat should be ~300 seconds (5 minutes)
        exp_minus_iat = claims["exp"] - claims["iat"]
        assert 250 <= exp_minus_iat <= 350


# ---------------------------------------------------------------------------
# Bcrypt Hashing
# ---------------------------------------------------------------------------

class TestBcryptHashing:
    """Token hashing with bcrypt."""

    @pytest.fixture
    def svc(self):
        return TokenService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
            )
        )

    def test_hash_token_produces_different_each_time(self):
        h1 = TokenService._hash_token("same-token")
        h2 = TokenService._hash_token("same-token")
        assert h1 != h2

    def test_verify_token_with_checkpw(self):
        raw = "test-raw-token"
        hashed = TokenService._hash_token(raw)
        raw_bytes = raw.encode("utf-8")[:72]
        assert bcrypt.checkpw(raw_bytes, hashed.encode()) is True

    def test_verify_token_wrong_value_fails(self):
        hashed = TokenService._hash_token("correct-token")
        wrong_bytes = "wrong-token".encode("utf-8")[:72]
        assert bcrypt.checkpw(wrong_bytes, hashed.encode()) is False

    def test_long_token_truncated_to_72_bytes(self):
        """Token longer than 72 bytes must be truncated before bcrypt."""
        long_token = "x" * 200
        hashed = TokenService._hash_token(long_token)
        raw_bytes = long_token.encode("utf-8")[:72]
        assert bcrypt.checkpw(raw_bytes, hashed.encode()) is True


# ---------------------------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    """Refresh token creation and rotation."""

    @pytest.fixture
    def svc(self):
        return TokenService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
                REFRESH_TOKEN_EXPIRE_DAYS=7,
            )
        )

    @pytest.mark.asyncio
    async def test_create_refresh_token_format(self, svc):
        """Creating a refresh token should return ``{user_id}.{secret}``."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        user_id = uuid.uuid4()

        raw_token = await svc.create_refresh_token(session, str(user_id))
        assert "." in raw_token
        assert raw_token.startswith(str(user_id))
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_with_valid_token(self, svc):
        """Valid token rotation should return a new token pair."""
        session = AsyncMock()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="refresh@test.com",
            name="Refresh",
            role=UserRole.CUSTOMER,
            preferred_lang="es",
            is_verified=False,
            created_at=datetime.now(timezone.utc),
        )

        # Create a token hash that will match
        raw = f"{user_id}.testsecret"
        token_hash = svc._hash_token(raw)

        # Mock: get_by_id returns user, then token query returns matching token
        svc._user_repo.get_by_id = AsyncMock(return_value=user)

        mock_scalars = MagicMock()
        # The RefreshToken mock
        mock_rt = MagicMock()
        mock_rt.token_hash = token_hash
        mock_rt.user_id = user_id
        mock_scalars.all.return_value = [mock_rt]

        mock_result = _make_unique_mock()
        mock_result.scalars.return_value = mock_scalars

        session.execute = AsyncMock(return_value=mock_result)

        result = await svc.refresh(session, RefreshRequest(refresh_token=raw))
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user is not None
        # Verify old token was deleted
        session.delete.assert_called_once_with(mock_rt)

    @pytest.mark.asyncio
    async def test_replay_detection_revokes_tokens(self, svc):
        """When a token is not found (already rotated), all user tokens
        must be revoked."""
        session = AsyncMock()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="replay@test.com",
            name="Replay",
            role=UserRole.CUSTOMER,
            preferred_lang="es",
            is_verified=False,
            created_at=datetime.now(timezone.utc),
        )

        # Mock: first execute → user found, second execute → no matching token
        execute_calls = []
        # call 0: get_by_id returns user (via user_repo, not session.execute)
        svc._user_repo.get_by_id = AsyncMock(return_value=user)

        # call via session.execute #1: find active tokens (returns empty)
        call_1 = _make_unique_mock()
        call_1_scalars = MagicMock()
        call_1_scalars.all.return_value = []
        call_1.scalars.return_value = call_1_scalars
        execute_calls.append(call_1)

        # call via session.execute #2: revoke_all → select tokens for user (empty)
        call_2 = _make_unique_mock()
        call_2_scalars = MagicMock()
        call_2_scalars.all.return_value = []
        call_2.scalars.return_value = call_2_scalars
        execute_calls.append(call_2)

        session.execute = AsyncMock(side_effect=execute_calls)

        with pytest.raises(ValueError, match="invalid or expired"):
            raw = f"{user_id}.fakesecret"
            await svc.refresh(session, RefreshRequest(refresh_token=raw))

        # Verify revoke_all was attempted (execute was called for revocation)
        assert session.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_refresh_invalid_format_returns_401(self, svc):
        session = AsyncMock()
        with pytest.raises(ValueError, match="invalid refresh token"):
            await svc.refresh(
                session, RefreshRequest(refresh_token="bad-format-no-dot")
            )


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    """Refresh token revocation on logout."""

    @pytest.fixture
    def svc(self):
        return TokenService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
            )
        )

    @pytest.mark.asyncio
    async def test_logout_successful(self, svc):
        """Valid token should be deleted on logout."""
        session = AsyncMock()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        user_id = uuid.uuid4()
        raw = f"{user_id}.testsecret"
        token_hash = svc._hash_token(raw)

        mock_rt = MagicMock()
        mock_rt.token_hash = token_hash
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_rt]
        mock_result = _make_unique_mock()
        mock_result.scalars.return_value = mock_scalars

        session.execute = AsyncMock(return_value=mock_result)

        await svc.logout(session, raw)
        session.delete.assert_called_once_with(mock_rt)

    @pytest.mark.asyncio
    async def test_logout_invalid_format_silent(self, svc):
        """Malformed token should silently return without error."""
        session = AsyncMock()
        await svc.logout(session, "bad-format")
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_logout_no_match_silent(self, svc):
        """Token that doesn't match any stored hash should be idempotent."""
        session = AsyncMock()
        user_id = uuid.uuid4()
        raw = f"{user_id}.unknownsecret"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = _make_unique_mock()
        mock_result.scalars.return_value = mock_scalars

        session.execute = AsyncMock(return_value=mock_result)

        await svc.logout(session, raw)
        session.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Extract User ID
# ---------------------------------------------------------------------------

class TestExtractUserId:
    """Token parsing edge cases."""

    def test_valid_token_format(self):
        svc = TokenService()
        uid = uuid.uuid4()
        token = f"{uid}.secret123"
        assert svc._extract_user_id(token) == uid

    def test_invalid_uuid_returns_none(self):
        svc = TokenService()
        assert svc._extract_user_id("not-a-uuid.secret") is None

    def test_no_dot_returns_none(self):
        svc = TokenService()
        assert svc._extract_user_id("justastring") is None

    def test_empty_string_returns_none(self):
        svc = TokenService()
        assert svc._extract_user_id("") is None
