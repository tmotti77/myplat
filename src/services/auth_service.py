"""Authentication service for user management."""
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.auth import (
    create_access_token, create_refresh_token, 
    verify_password, get_password_hash,
    authenticate_user, get_user_by_email, create_user
)
from ..models.user import User


class AuthService:
    """Service for handling authentication operations."""
    
    async def login(self, db: AsyncSession, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        user = await get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Update last login
        user.last_login_at = datetime.utcnow().isoformat() + "Z"
        await db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
            }
        }
    
    async def register(self, db: AsyncSession, email: str, password: str, full_name: str = None) -> dict:
        """Register a new user."""
        # Check if user already exists
        existing_user = await get_user_by_email(db, email)
        if existing_user:
            raise ValueError("User already exists")
        
        # Create new user
        user = await create_user(
            db=db,
            email=email,
            password=password,
            full_name=full_name or email.split('@')[0],
            is_active=True,
            is_superuser=False
        )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
            }
        }
    
    async def refresh_token(self, db: AsyncSession, user_id: str) -> dict:
        """Refresh access token."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }


# Global instance
auth_service = AuthService()