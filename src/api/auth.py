"""Authentication and authorization endpoints."""

from datetime import timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import get_current_user, get_current_active_user
from ..models.user import User, UserRole
from ..models.tenant import Tenant
from ..services.auth_service import AuthService
from ..middleware.dependencies import get_auth_service

router = APIRouter()
security = HTTPBearer()


# Request/Response models
class UserRegister(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    tenant_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    tenant_id: str
    created_at: str

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check username availability
        existing_username = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing_username.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create or get tenant
        tenant = None
        if user_data.tenant_name:
            # Create new tenant
            tenant = Tenant(
                name=user_data.tenant_name,
                domain=f"{user_data.tenant_name.lower().replace(' ', '-')}.example.com",
                is_active=True
            )
            db.add(tenant)
            await db.flush()
        else:
            # Use default tenant or create one
            default_tenant = await db.execute(
                select(Tenant).where(Tenant.name == "Default")
            )
            tenant = default_tenant.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(
                    name="Default",
                    domain="default.example.com",
                    is_active=True
                )
                db.add(tenant)
                await db.flush()
        
        # Create user
        hashed_password = auth_service.hash_password(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            tenant_id=tenant.id,
            role=UserRole.USER,
            is_active=True,
            is_verified=False  # Require email verification
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "email_verification_required": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return tokens."""
    try:
        # Find user by email
        query = select(User).options(selectinload(User.tenant)).where(User.email == user_data.email)
        if user_data.tenant_id:
            query = query.where(User.tenant_id == user_data.tenant_id)
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not auth_service.verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Check if tenant is active
        if not user.tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant is deactivated"
            )
        
        # Create tokens
        access_token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "tenant_id": user.tenant_id
        }
        
        access_token = auth_service.create_access_token(
            data=access_token_data,
            expires_delta=timedelta(hours=24)
        )
        
        refresh_token = auth_service.create_refresh_token(user.id)
        
        # Store refresh token in Redis
        await auth_service.store_refresh_token(user.id, refresh_token)
        
        # Set secure HTTP-only cookie for refresh token
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=60 * 60 * 24 * 30  # 30 days
        )
        
        # Log successful login
        await auth_service.log_login_attempt(user.id, request.client.host, True)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=60 * 60 * 24  # 24 hours
        )
        
    except HTTPException:
        # Log failed login attempt
        if user_data.email:
            await auth_service.log_login_attempt(None, request.client.host, False, user_data.email)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = auth_service.verify_refresh_token(token_data.refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token exists in Redis
        stored_token = await auth_service.get_stored_refresh_token(user_id)
        if not stored_token or stored_token != token_data.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "tenant_id": user.tenant_id
        }
        
        access_token = auth_service.create_access_token(
            data=access_token_data,
            expires_delta=timedelta(hours=24)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=token_data.refresh_token,
            expires_in=60 * 60 * 24  # 24 hours
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout_user(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user and invalidate tokens."""
    try:
        # Remove refresh token from Redis
        await auth_service.revoke_refresh_token(current_user.id)
        
        # Clear refresh token cookie
        response.delete_cookie("refresh_token")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information."""
    try:
        # Update allowed fields
        allowed_fields = {"full_name", "preferences"}
        
        for field, value in user_update.items():
            if field in allowed_fields:
                setattr(current_user, field, value)
        
        await db.commit()
        await db.refresh(current_user)
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    passwords: Dict[str, str],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password."""
    try:
        current_password = passwords.get("current_password")
        new_password = passwords.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current and new passwords are required"
            )
        
        # Verify current password
        if not auth_service.verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = auth_service.hash_password(new_password)
        current_user.hashed_password = new_hashed_password
        
        await db.commit()
        
        # Revoke all refresh tokens to force re-login
        await auth_service.revoke_all_refresh_tokens(current_user.id)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )