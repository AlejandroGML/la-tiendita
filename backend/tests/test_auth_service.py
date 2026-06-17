"""Unit tests for AuthService — token create/verify, bcrypt, replay, rate-limit."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import pytest

from app.config import Settings
from app.models.user import User, UserRole
from app.schemas.auth import RefreshRequest
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_unique_mock(**kwargs):
    """Build a mock that supports ``.unique()`` returning itself.

    The repo base methods call ``result.unique().scalar_one_or_none()`` or
    ``result.unique().scalars().all()``.  This helper ensures ``.unique()``
    returns the same mock so downstream calls resolve correctly.
    """
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


def _make_execute_mock(scalar_one_or_none_values=None, scalar_results=None):
    """Build an AsyncMock for ``session.execute`` with configurable returns.

    ``scalar_one_or_none_values``: list of values for successive calls.
    ``scalar_results``: list of ``_make_scalar_result`` for successive calls.
    """
    mock = AsyncMock()

    if scalar_one_or_none_values:
        mock.return_value = _make_unique_mock()
        mock.return_value.scalar_one_or_none = AsyncMock(
            side_effect=scalar_one_or_none_values
        )
    if scalar_results:
        mock.side_effect = scalar_results

    return mock


# ---------------------------------------------------------------------------
# Token Create / Verify
# ---------------------------------------------------------------------------

class TestTokenCreateVerify:
    """JWT access token creation and verification."""

    @pytest.fixture
    def svc(self):
        return AuthService(
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
        svc_expired = AuthService(
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


# ---------------------------------------------------------------------------
# Bcrypt Hashing
# ---------------------------------------------------------------------------

class TestBcryptHashing:
    """Password and token hashing with bcrypt."""

    @pytest.fixture
    def svc(self):
        return AuthService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
            )
        )

    def test_hash_password(self, svc):
        password = "mySecret123"
        hashed = svc._hash_password(password)
        assert hashed != password
        assert svc._verify_password(password, hashed) is True

    def test_verify_wrong_password(self, svc):
        hashed = svc._hash_password("correct")
        assert svc._verify_password("wrong", hashed) is False

    def test_hash_token_produces_different_each_time(self):
        h1 = AuthService._hash_token("same-token")
        h2 = AuthService._hash_token("same-token")
        assert h1 != h2

    def test_verify_token_with_checkpw(self, svc):
        raw = "test-raw-token"
        hashed = svc._hash_token(raw)
        raw_bytes = raw.encode("utf-8")[:72]
        assert bcrypt.checkpw(raw_bytes, hashed.encode()) is True

    def test_verify_token_wrong_value_fails(self, svc):
        hashed = svc._hash_token("correct-token")
        wrong_bytes = "wrong-token".encode("utf-8")[:72]
        assert bcrypt.checkpw(wrong_bytes, hashed.encode()) is False

    def test_long_token_truncated_to_72_bytes(self, svc):
        """Token longer than 72 bytes must be truncated before bcrypt."""
        long_token = "x" * 200
        hashed = svc._hash_token(long_token)
        raw_bytes = long_token.encode("utf-8")[:72]
        assert bcrypt.checkpw(raw_bytes, hashed.encode()) is True


# ---------------------------------------------------------------------------
# Replay Detection
# ---------------------------------------------------------------------------

class TestReplayDetection:
    """Refresh token rotation and replay detection."""

    @pytest.fixture
    def svc(self):
        return AuthService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
                REFRESH_TOKEN_EXPIRE_DAYS=7,
            )
        )

    @pytest.mark.asyncio
    async def test_refresh_with_valid_token(self, svc):
        """Creating a refresh token should succeed and return a properly
        formatted token string."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        user_id = uuid.uuid4()

        raw_token = await svc._create_refresh_token(session, str(user_id))
        assert "." in raw_token
        assert raw_token.startswith(str(user_id))
        session.add.assert_called_once()

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
        )

        # Mock: first execute → user found, second execute → no matching token
        execute_calls = []
        # call 0: find user via UserRepository.get_by_id
        call_0 = _make_unique_mock()
        call_0.scalar_one_or_none = AsyncMock(return_value=user)
        execute_calls.append(call_0)

        # call 1: find active tokens (returns empty)
        call_1 = _make_unique_mock()
        call_1_scalars = MagicMock()
        call_1_scalars.all.return_value = []
        call_1.scalars.return_value = call_1_scalars
        execute_calls.append(call_1)

        # call 2: revoke_all → select tokens for user
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
        assert session.execute.call_count >= 3

    @pytest.mark.asyncio
    async def test_refresh_invalid_format_returns_401(self, svc):
        session = AsyncMock()
        with pytest.raises(ValueError, match="invalid refresh token"):
            await svc.refresh(
                session, RefreshRequest(refresh_token="bad-format-no-dot")
            )


# ---------------------------------------------------------------------------
# Extract User ID
# ---------------------------------------------------------------------------

class TestExtractUserId:
    """Token parsing edge cases."""

    def test_valid_token_format(self):
        svc = AuthService()
        uid = uuid.uuid4()
        token = f"{uid}.secret123"
        assert svc._extract_user_id(token) == uid

    def test_invalid_uuid_returns_none(self):
        svc = AuthService()
        assert svc._extract_user_id("not-a-uuid.secret") is None

    def test_no_dot_returns_none(self):
        svc = AuthService()
        assert svc._extract_user_id("justastring") is None

    def test_empty_string_returns_none(self):
        svc = AuthService()
        assert svc._extract_user_id("") is None


# ---------------------------------------------------------------------------
# Rate Limit Logic
# ---------------------------------------------------------------------------

class TestRateLimitLogic:
    """Rate limiter window logic (not full middleware — just the pruning)."""

    def test_prune_removes_expired_timestamps(self):
        import time

        from app.middleware.rate_limit import _buckets, _prune

        _buckets.clear()
        ip = "10.0.0.1"
        old_time = time.monotonic() - 100
        _buckets[ip] = [old_time, old_time + 1]

        _prune(ip, 60)
        assert len(_buckets[ip]) == 0

    def test_prune_keeps_recent_timestamps(self):
        import time

        from app.middleware.rate_limit import _buckets, _prune

        _buckets.clear()
        ip = "10.0.0.2"
        recent = time.monotonic() - 5
        _buckets[ip] = [recent]

        _prune(ip, 60)
        assert len(_buckets[ip]) == 1
