"""
Unit tests for AuthService
Tests authentication, authorization, token management, and security features
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import uuid
import jwt
from passlib.context import CryptContext

from src.services.auth_service import AuthService
from src.models.user import User, UserRole
from src.models.tenant import Tenant
from src.core.config import settings
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError,
    UserNotFoundError,
    UserInactiveError
)

@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test suite for AuthService functionality."""
    
    @pytest_asyncio.fixture
    async def auth_service(self, db_session, redis_client):
        """Create AuthService instance for testing."""
        return AuthService(db=db_session, redis=redis_client)
    
    @pytest_asyncio.fixture
    async def sample_user(self, db_session, test_tenant):
        """Create a sample user for testing."""
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            username="testuser",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            full_name="Test User",
            tenant_id=test_tenant.id,
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @pytest.mark.asyncio
    async def test_hash_password(self, auth_service):
        """Test password hashing functionality."""
        password = "testpassword123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50
    
    @pytest.mark.asyncio
    async def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "testpassword123"
        hashed = auth_service.hash_password(password)
        
        # Valid password
        assert auth_service.verify_password(password, hashed) is True
        
        # Invalid password
        assert auth_service.verify_password("wrongpassword", hashed) is False
        assert auth_service.verify_password("", hashed) is False
        assert auth_service.verify_password(None, hashed) is False
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service):
        """Test access token creation."""
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        
        token = auth_service.create_access_token(
            data={"sub": user_id, "tenant_id": tenant_id}
        )
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Decode and verify token content
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == user_id
        assert decoded["tenant_id"] == tenant_id
        assert "exp" in decoded
        assert "iat" in decoded
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        user_id = str(uuid.uuid4())
        
        token = auth_service.create_refresh_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Verify token structure
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == user_id
        assert decoded["type"] == "refresh"
    
    @pytest.mark.asyncio
    async def test_verify_token_valid(self, auth_service):
        """Test token verification with valid token."""
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        
        token = auth_service.create_access_token(
            data={"sub": user_id, "tenant_id": tenant_id}
        )
        
        payload = auth_service.verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["tenant_id"] == tenant_id
    
    @pytest.mark.asyncio
    async def test_verify_token_expired(self, auth_service):
        """Test token verification with expired token."""
        user_id = str(uuid.uuid4())
        
        # Create expired token
        with patch('src.services.auth_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(hours=2)
            token = auth_service.create_access_token(
                data={"sub": user_id},
                expires_delta=timedelta(minutes=30)
            )
        
        with pytest.raises(TokenExpiredError):
            auth_service.verify_token(token)
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token."""
        with pytest.raises(InvalidTokenError):
            auth_service.verify_token("invalid.token.here")
        
        with pytest.raises(InvalidTokenError):
            auth_service.verify_token("")
        
        with pytest.raises(InvalidTokenError):
            auth_service.verify_token(None)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, sample_user):
        """Test successful user authentication."""
        user = await auth_service.authenticate_user(
            email="test@example.com",
            password="secret",  # This matches the hashed password in sample_user
            tenant_id=sample_user.tenant_id
        )
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, sample_user):
        """Test authentication with wrong password."""
        user = await auth_service.authenticate_user(
            email="test@example.com",
            password="wrongpassword",
            tenant_id=sample_user.tenant_id
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, test_tenant):
        """Test authentication with non-existent user."""
        user = await auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="password",
            tenant_id=test_tenant.id
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, db_session, test_tenant):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User(
            id=str(uuid.uuid4()),
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            full_name="Inactive User",
            tenant_id=test_tenant.id,
            role=UserRole.USER,
            is_active=False,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        user = await auth_service.authenticate_user(
            email="inactive@example.com",
            password="secret",
            tenant_id=test_tenant.id
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_service, sample_user):
        """Test getting current user with valid token."""
        token = auth_service.create_access_token(
            data={"sub": sample_user.id, "tenant_id": sample_user.tenant_id}
        )
        
        user = await auth_service.get_current_user(token)
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_service):
        """Test getting current user with invalid token."""
        with pytest.raises(InvalidTokenError):
            await auth_service.get_current_user("invalid.token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, auth_service):
        """Test getting current user when user doesn't exist."""
        fake_user_id = str(uuid.uuid4())
        token = auth_service.create_access_token(
            data={"sub": fake_user_id, "tenant_id": str(uuid.uuid4())}
        )
        
        with pytest.raises(UserNotFoundError):
            await auth_service.get_current_user(token)
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self, auth_service, sample_user, redis_client):
        """Test refreshing access token."""
        refresh_token = auth_service.create_refresh_token(sample_user.id)
        
        # Store refresh token in Redis
        await redis_client.setex(
            f"refresh_token:{sample_user.id}",
            timedelta(days=7).total_seconds(),
            refresh_token
        )
        
        new_access_token = await auth_service.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert len(new_access_token) > 100
        
        # Verify new token
        payload = auth_service.verify_token(new_access_token)
        assert payload["sub"] == sample_user.id
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, auth_service):
        """Test refreshing with invalid refresh token."""
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("invalid.refresh.token")
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_not_stored(self, auth_service, sample_user):
        """Test refreshing with token not stored in Redis."""
        refresh_token = auth_service.create_refresh_token(sample_user.id)
        
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token(refresh_token)
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token(self, auth_service, sample_user, redis_client):
        """Test revoking refresh token."""
        refresh_token = auth_service.create_refresh_token(sample_user.id)
        
        # Store refresh token
        await redis_client.setex(
            f"refresh_token:{sample_user.id}",
            timedelta(days=7).total_seconds(),
            refresh_token
        )
        
        # Revoke token
        await auth_service.revoke_refresh_token(sample_user.id)
        
        # Verify token is removed
        stored_token = await redis_client.get(f"refresh_token:{sample_user.id}")
        assert stored_token is None
    
    @pytest.mark.asyncio
    async def test_check_permissions_admin(self, auth_service, db_session, test_tenant):
        """Test permission checking for admin user."""
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@example.com",
            username="adminuser",
            hashed_password="hashed",
            full_name="Admin User",
            tenant_id=test_tenant.id,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db_session.add(admin_user)
        await db_session.commit()
        
        # Admin should have all permissions
        assert auth_service.check_permissions(admin_user, ["read", "write", "admin"]) is True
        assert auth_service.check_permissions(admin_user, ["manage_users"]) is True
        assert auth_service.check_permissions(admin_user, ["delete_tenant"]) is True
    
    @pytest.mark.asyncio
    async def test_check_permissions_user(self, auth_service, sample_user):
        """Test permission checking for regular user."""
        # Regular user should have basic permissions
        assert auth_service.check_permissions(sample_user, ["read"]) is True
        assert auth_service.check_permissions(sample_user, ["write"]) is True
        
        # But not admin permissions
        assert auth_service.check_permissions(sample_user, ["admin"]) is False
        assert auth_service.check_permissions(sample_user, ["manage_users"]) is False
    
    @pytest.mark.asyncio
    async def test_check_permissions_inactive_user(self, auth_service, db_session, test_tenant):
        """Test permission checking for inactive user."""
        inactive_user = User(
            id=str(uuid.uuid4()),
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password="hashed",
            full_name="Inactive User",
            tenant_id=test_tenant.id,
            role=UserRole.USER,
            is_active=False,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        # Inactive user should have no permissions
        assert auth_service.check_permissions(inactive_user, ["read"]) is False
        assert auth_service.check_permissions(inactive_user, ["write"]) is False
    
    @pytest.mark.asyncio
    async def test_validate_tenant_access(self, auth_service, sample_user):
        """Test tenant access validation."""
        # User should have access to their own tenant
        assert auth_service.validate_tenant_access(sample_user, sample_user.tenant_id) is True
        
        # User should not have access to other tenants
        other_tenant_id = str(uuid.uuid4())
        assert auth_service.validate_tenant_access(sample_user, other_tenant_id) is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, auth_service, redis_client):
        """Test rate limiting functionality."""
        client_id = "test_client"
        limit = 5
        window = 60  # seconds
        
        # Should allow requests under limit
        for i in range(limit):
            allowed = await auth_service.check_rate_limit(client_id, limit, window)
            assert allowed is True
        
        # Should block requests over limit
        blocked = await auth_service.check_rate_limit(client_id, limit, window)
        assert blocked is False
    
    @pytest.mark.asyncio
    async def test_session_management(self, auth_service, sample_user, redis_client):
        """Test user session management."""
        session_id = str(uuid.uuid4())
        
        # Create session
        await auth_service.create_session(sample_user.id, session_id)
        
        # Verify session exists
        sessions = await auth_service.get_active_sessions(sample_user.id)
        assert session_id in sessions
        
        # Revoke session
        await auth_service.revoke_session(sample_user.id, session_id)
        
        # Verify session is removed
        sessions = await auth_service.get_active_sessions(sample_user.id)
        assert session_id not in sessions
    
    @pytest.mark.asyncio
    async def test_security_headers(self, auth_service):
        """Test security header validation."""
        # Test CSRF token validation
        csrf_token = auth_service.generate_csrf_token()
        assert isinstance(csrf_token, str)
        assert len(csrf_token) > 20
        
        # Test Content Security Policy
        csp_header = auth_service.get_csp_header()
        assert "default-src 'self'" in csp_header
        assert "script-src" in csp_header
        assert "style-src" in csp_header
    
    @pytest.mark.asyncio
    async def test_two_factor_auth(self, auth_service, sample_user):
        """Test two-factor authentication."""
        # Generate 2FA secret
        secret = auth_service.generate_2fa_secret()
        assert isinstance(secret, str)
        assert len(secret) == 32
        
        # Enable 2FA for user
        await auth_service.enable_2fa(sample_user.id, secret)
        
        # Verify 2FA is enabled
        user_2fa = await auth_service.get_2fa_status(sample_user.id)
        assert user_2fa["enabled"] is True
        assert user_2fa["secret"] == secret
        
        # Disable 2FA
        await auth_service.disable_2fa(sample_user.id)
        
        # Verify 2FA is disabled
        user_2fa = await auth_service.get_2fa_status(sample_user.id)
        assert user_2fa["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_password_reset(self, auth_service, sample_user, redis_client):
        """Test password reset functionality."""
        # Generate reset token
        reset_token = await auth_service.generate_password_reset_token(sample_user.email)
        assert isinstance(reset_token, str)
        
        # Verify token is stored in Redis
        stored_data = await redis_client.get(f"password_reset:{reset_token}")
        assert stored_data is not None
        
        # Reset password
        new_password = "newpassword123"
        success = await auth_service.reset_password(reset_token, new_password)
        assert success is True
        
        # Verify old password doesn't work
        auth_result = await auth_service.authenticate_user(
            sample_user.email, "secret", sample_user.tenant_id
        )
        assert auth_result is None
        
        # Verify new password works
        auth_result = await auth_service.authenticate_user(
            sample_user.email, new_password, sample_user.tenant_id
        )
        assert auth_result is not None
    
    @pytest.mark.asyncio
    async def test_account_lockout(self, auth_service, sample_user, redis_client):
        """Test account lockout functionality."""
        email = sample_user.email
        
        # Simulate failed login attempts
        max_attempts = 5
        for i in range(max_attempts):
            await auth_service.record_failed_login(email)
        
        # Account should be locked
        is_locked = await auth_service.is_account_locked(email)
        assert is_locked is True
        
        # Authentication should fail even with correct password
        auth_result = await auth_service.authenticate_user(
            email, "secret", sample_user.tenant_id
        )
        assert auth_result is None
        
        # Unlock account
        await auth_service.unlock_account(email)
        
        # Authentication should work again
        auth_result = await auth_service.authenticate_user(
            email, "secret", sample_user.tenant_id
        )
        assert auth_result is not None