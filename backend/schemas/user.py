"""
Pydantic schemas for User authentication and management.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base User schema with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(
        ..., min_length=3, max_length=100, description="Unique username"
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="User's full name"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User's password")
    bio: Optional[str] = Field(None, description="User's biography")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: Optional[EmailStr] = Field(None, description="User's email address")
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Unique username"
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="User's full name"
    )
    bio: Optional[str] = Field(None, description="User's biography")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    email_notifications: Optional[bool] = Field(
        None, description="Enable email notifications"
    )


class UserLogin(BaseModel):
    """Schema for user login."""

    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User's password")


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="User's unique ID")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user's email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    bio: Optional[str] = Field(None, description="User's biography")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    email_notifications: bool = Field(..., description="Email notifications setting")


class UserInDB(UserResponse):
    """Schema for user data as stored in database (includes sensitive fields)."""

    hashed_password: str = Field(..., description="Hashed password")
    is_superuser: bool = Field(..., description="Whether the user has admin privileges")


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Schema for token payload data."""

    user_id: Optional[int] = Field(None, description="User ID from token")
    username: Optional[str] = Field(None, description="Username from token")


class PasswordChange(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class PasswordReset(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., description="Email address for password reset")
