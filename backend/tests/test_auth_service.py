"""Unit tests for AuthService — register, login, admin_login, verify_2fa,
password hashing, TOTP verification.

Token creation/verification tests moved to ``test_token_service.py``.
Refresh/logout/forgot/reset tests moved to respective test files.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import pytest

from app.config import Settings
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.schemas.auth import LoginRequest, RegisterRequest, Verify2faRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id=None, role=UserRole.CUSTOMER, totp_enabled=False):
    return User(
        id=user_id or uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        role=role,
        password_hash="$2b$12$abcdefghijklmnopqrstuvwx1234567890123456789012345678901",
        totp_enabled=totp_enabled,
        totp_secret="JBSWY3DPEHPK3PXP" if totp_enabled else None,
        preferred_lang="es",
        is_verified=False,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    """AuthService with a real TokenService but mocked session/repo."""
    return AuthService(
        app_settings=Settings(
            DATABASE_URL="postgresql+asyncpg:///test",
            SECRET_KEY="test-secret-key-for-unit-tests",
            ACCESS_TOKEN_EXPIRE_MINUTES=15,
            REFRESH_TOKEN_EXPIRE_DAYS=7,
            JWT_ALGORITHM="HS256",
        ),
    )


@pytest.fixture
def mock_session():
    return AsyncMock()


# ---------------------------------------------------------------------------
# Constructor / Injection
# ---------------------------------------------------------------------------

class TestConstructor:
    """AuthService constructor and dependency injection."""

    def test_injects_default_token_service(self):
        """AuthService should create a default TokenService when none given."""
        svc = AuthService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
            )
        )
        assert svc._token_service is not None
        assert isinstance(svc._token_service, TokenService)

    def test_injects_custom_token_service(self):
        """AuthService should use a provided TokenService instance."""
        mock_ts = MagicMock(spec=TokenService)
        svc = AuthService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
            ),
            token_service=mock_ts,
        )
        assert svc._token_service is mock_ts


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:
    """User registration — creates user, issues tokens, emits event."""

    @pytest.mark.asyncio
    async def test_register_creates_user_and_issues_tokens(
        self, svc, mock_session
    ):
        """Successful registration should create user, issue tokens, emit event."""
        svc._user_repo.get_by_email = AsyncMock(return_value=None)
        svc._token_service.create_access_token = MagicMock(
            return_value="fake.access.jwt"
        )
        svc._token_service.create_refresh_token = AsyncMock(
            return_value="fake.refresh.token"
        )

        svc._hash_password = MagicMock(return_value="hashed-password")

        # Capture the user object added to session and populate SQLAlchemy
        # defaults (id, created_at) on flush — these are normally populated
        # by the DB at INSERT time.
        captured_user = None

        def capture_user(user):
            nonlocal captured_user
            captured_user = user

        async def flush_with_defaults():
            if captured_user is not None:
                if captured_user.id is None:
                    captured_user.id = uuid.uuid4()
                if captured_user.created_at is None:
                    captured_user.created_at = datetime.now(timezone.utc)

        mock_session.add = MagicMock(side_effect=capture_user)
        mock_session.flush = AsyncMock(side_effect=flush_with_defaults)

        data = RegisterRequest(
            email="new@test.com",
            password="SecurePass1",
            name="New User",
        )

        result = await svc.register(mock_session, data)

        assert result.access_token == "fake.access.jwt"
        assert result.refresh_token == "fake.refresh.token"
        assert result.user.email == "new@test.com"
        svc._token_service.create_access_token.assert_called_once_with(
            str(captured_user.id), "customer"
        )
        svc._token_service.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self, svc, mock_session):
        """Registering with an existing email should raise ValueError."""
        existing = _make_user()
        svc._user_repo.get_by_email = AsyncMock(return_value=existing)

        data = RegisterRequest(
            email="existing@test.com",
            password="SecurePass1",
            name="Duplicate",
        )

        with pytest.raises(ValueError, match="email already registered"):
            await svc.register(mock_session, data)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    """User login — verifies credentials and issues tokens."""

    @pytest.mark.asyncio
    async def test_login_successful(self, svc, mock_session):
        """Valid credentials should return a token pair."""
        user = _make_user()
        svc._user_repo.get_by_email = AsyncMock(return_value=user)
        svc._verify_password = MagicMock(return_value=True)
        svc._token_service.create_access_token = MagicMock(
            return_value="fake.access.jwt"
        )
        svc._token_service.create_refresh_token = AsyncMock(
            return_value="fake.refresh.token"
        )

        data = LoginRequest(email="test@example.com", password="correct")
        result = await svc.login(mock_session, data)

        assert result.access_token == "fake.access.jwt"
        assert result.refresh_token == "fake.refresh.token"
        svc._token_service.create_access_token.assert_called_once()
        svc._token_service.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_email_raises(self, svc, mock_session):
        """Unknown email should raise ValueError."""
        svc._user_repo.get_by_email = AsyncMock(return_value=None)

        data = LoginRequest(email="unknown@test.com", password="any")
        with pytest.raises(ValueError, match="invalid email or password"):
            await svc.login(mock_session, data)

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self, svc, mock_session):
        """Wrong password should raise ValueError."""
        user = _make_user()
        svc._user_repo.get_by_email = AsyncMock(return_value=user)
        svc._verify_password = MagicMock(return_value=False)

        data = LoginRequest(email="test@example.com", password="wrong")
        with pytest.raises(ValueError, match="invalid email or password"):
            await svc.login(mock_session, data)


# ---------------------------------------------------------------------------
# Admin Login
# ---------------------------------------------------------------------------

class TestAdminLogin:
    """Admin login — 2FA flow and direct token issuance."""

    @pytest.mark.asyncio
    async def test_admin_login_no_2fa_issues_tokens(
        self, svc, mock_session
    ):
        """Admin without 2FA should receive tokens directly."""
        user = _make_user(role=UserRole.ADMIN, totp_enabled=False)
        svc._user_repo.get_by_email = AsyncMock(return_value=user)
        svc._verify_password = MagicMock(return_value=True)
        svc._token_service.create_access_token = MagicMock(
            return_value="fake.access.jwt"
        )
        svc._token_service.create_refresh_token = AsyncMock(
            return_value="fake.refresh.token"
        )

        data = LoginRequest(email="admin@test.com", password="adminpass")
        result = await svc.admin_login(mock_session, data)

        assert result.access_token == "fake.access.jwt"
        assert result.refresh_token == "fake.refresh.token"
        svc._token_service.create_access_token.assert_called_once()
        svc._token_service.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_login_with_2fa_returns_login_token(
        self, svc, mock_session
    ):
        """Admin with 2FA should get a login_token instead of tokens."""
        user = _make_user(role=UserRole.ADMIN, totp_enabled=True)
        svc._user_repo.get_by_email = AsyncMock(return_value=user)
        svc._verify_password = MagicMock(return_value=True)
        svc._token_service.create_login_token = MagicMock(
            return_value="fake.login.jwt"
        )

        data = LoginRequest(email="admin@test.com", password="adminpass")
        result = await svc.admin_login(mock_session, data)

        assert result.require_2fa is True
        assert result.login_token == "fake.login.jwt"
        assert result.user is not None
        svc._token_service.create_login_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_login_non_admin_raises(self, svc, mock_session):
        """Non-admin user trying admin_login should raise ValueError."""
        user = _make_user(role=UserRole.CUSTOMER)
        svc._user_repo.get_by_email = AsyncMock(return_value=user)
        svc._verify_password = MagicMock(return_value=True)

        data = LoginRequest(email="user@test.com", password="userpass")
        with pytest.raises(ValueError, match="not an admin account"):
            await svc.admin_login(mock_session, data)


# ---------------------------------------------------------------------------
# Verify 2FA
# ---------------------------------------------------------------------------

class TestVerify2FA:
    """2FA verification — validates login_token and TOTP, then issues tokens."""

    @pytest.mark.asyncio
    async def test_verify_2fa_successful(self, svc, mock_session):
        """Valid login_token + correct TOTP should issue tokens."""
        user_id = uuid.uuid4()
        user = _make_user(user_id=user_id, role=UserRole.ADMIN, totp_enabled=True)

        svc._token_service.verify_access_token = MagicMock(
            return_value={"sub": str(user_id)}
        )
        svc._user_repo.get_by_id = AsyncMock(return_value=user)
        svc._verify_totp = MagicMock(return_value=True)
        svc._token_service.create_access_token = MagicMock(
            return_value="fake.access.jwt"
        )
        svc._token_service.create_refresh_token = AsyncMock(
            return_value="fake.refresh.token"
        )

        data = Verify2faRequest(login_token="fake.jwt", code="123456")
        result = await svc.verify_2fa(mock_session, data)

        assert result.access_token == "fake.access.jwt"
        assert result.refresh_token == "fake.refresh.token"
        svc._token_service.verify_access_token.assert_called_once_with(
            "fake.jwt"
        )
        svc._token_service.create_access_token.assert_called_once()
        svc._token_service.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_2fa_invalid_token_raises(self, svc, mock_session):
        """Invalid login_token should raise ValueError."""
        svc._token_service.verify_access_token = MagicMock(return_value=None)

        data = Verify2faRequest(login_token="bad.jwt", code="123456")
        with pytest.raises(ValueError, match="invalid or expired login token"):
            await svc.verify_2fa(mock_session, data)

    @pytest.mark.asyncio
    async def test_verify_2fa_wrong_code_raises(self, svc, mock_session):
        """Wrong TOTP code should raise ValueError."""
        user_id = uuid.uuid4()
        user = _make_user(user_id=user_id, role=UserRole.ADMIN, totp_enabled=True)

        svc._token_service.verify_access_token = MagicMock(
            return_value={"sub": str(user_id)}
        )
        svc._user_repo.get_by_id = AsyncMock(return_value=user)
        svc._verify_totp = MagicMock(return_value=False)

        data = Verify2faRequest(login_token="fake.jwt", code="000000")
        with pytest.raises(ValueError, match="invalid verification code"):
            await svc.verify_2fa(mock_session, data)


# ---------------------------------------------------------------------------
# Password Hashing (retained in AuthService)
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    """Password hashing and verification — retained in AuthService."""

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


# ---------------------------------------------------------------------------
# TOTP Verification (retained in AuthService)
# ---------------------------------------------------------------------------

class TestTotpVerification:
    """TOTP 6-digit code verification — retained in AuthService."""

    @pytest.fixture
    def svc(self):
        return AuthService(
            app_settings=Settings(
                DATABASE_URL="postgresql+asyncpg:///test",
                SECRET_KEY="test-secret",
            )
        )

    def test_verify_totp_valid(self, svc):
        import pyotp

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert svc._verify_totp(secret, code) is True

    def test_verify_totp_invalid_code(self, svc):
        assert svc._verify_totp("JBSWY3DPEHPK3PXP", "000000") is False

    def test_verify_totp_invalid_secret_returns_false(self, svc):
        assert svc._verify_totp("", "123456") is False
