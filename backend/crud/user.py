"""
CRUD operations for User model.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.user import User
from schemas.user import UserCreate, UserUpdate
from auth.utils import hash_password, verify_password


class UserCRUD:
    """CRUD operations for User model."""

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_username_or_email(db: Session, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        return (
            db.query(User)
            .filter(or_(User.username == identifier, User.email == identifier))
            .first()
        )

    @staticmethod
    def get_users(
        db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[User]:
        """Get multiple users with pagination."""
        query = db.query(User)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user."""
        # Hash the password
        hashed_password = hash_password(user.password)

        # Create user instance
        db_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            bio=user.bio,
            avatar_url=user.avatar_url,
            is_active=True,
            is_verified=False,
            is_superuser=False,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(
        db: Session, user_id: int, user_update: UserUpdate
    ) -> Optional[User]:
        """Update an existing user."""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return None

        # Update fields that are provided
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user (soft delete by setting is_active=False)."""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.is_active = False
        db.commit()
        return True

    @staticmethod
    def authenticate_user(
        db: Session, identifier: str, password: str
    ) -> Optional[User]:
        """Authenticate user with username/email and password."""
        user = UserCRUD.get_user_by_username_or_email(db, identifier)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        return user

    @staticmethod
    def change_password(db: Session, user_id: int, new_password: str) -> bool:
        """Change user password."""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.hashed_password = hash_password(new_password)
        db.commit()
        return True

    @staticmethod
    def verify_user(db: Session, user_id: int) -> bool:
        """Mark user as verified."""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.is_verified = True
        db.commit()
        return True

    @staticmethod
    def make_superuser(db: Session, user_id: int) -> bool:
        """Make user a superuser."""
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if not db_user:
            return False

        db_user.is_superuser = True
        db.commit()
        return True


# Create a global instance for easy import
user_crud = UserCRUD()
