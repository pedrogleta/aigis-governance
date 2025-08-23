# User Authentication System

This directory contains a complete user authentication system for the Aigis Governance backend, implemented using PostgreSQL, SQLAlchemy, and Alembic for database migrations.

## Overview

The authentication system includes:

- **User Model**: SQLAlchemy model for user data with authentication fields
- **JWT Authentication**: Token-based authentication using JSON Web Tokens
- **Password Security**: Bcrypt hashing for secure password storage
- **Database Migrations**: Alembic for managing database schema changes
- **API Endpoints**: FastAPI routes for user registration, login, and management
- **Permission System**: Support for regular users, verified users, and superusers

## Directory Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration files
│   ├── env.py                # Alembic configuration
│   └── script.py.mako        # Migration template
├── alembic.ini                # Alembic settings
├── models/
│   └── user.py               # User SQLAlchemy model
├── schemas/
│   └── user.py               # Pydantic schemas for API
├── crud/
│   └── user.py               # Database operations
├── auth/
│   ├── utils.py              # Password hashing and JWT utilities
│   └── dependencies.py       # FastAPI authentication dependencies
└── api/
    └── auth.py               # Authentication API endpoints
```

## Setup Instructions

### 1. Install Dependencies

The required packages are already added to `pyproject.toml`:
- `alembic>=1.13.0` - Database migrations
- `bcrypt>=4.1.0` - Password hashing
- `passlib[bcrypt]>=1.7.4` - Password utilities
- `psycopg2-binary>=2.9.9` - PostgreSQL adapter
- `python-jose[cryptography]>=3.3.0` - JWT tokens
- `python-multipart>=0.0.6` - Form data support

### 2. Database Configuration

Update your `.env` file with PostgreSQL credentials:

```env
# PostgreSQL settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=aigis_governance

# Authentication settings
SECRET_KEY=your-super-secret-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Run Migrations

Initialize and run the database migrations:

```bash
cd backend

# Apply the migration to create the users table
alembic upgrade head
```

### 4. Create a Superuser (Optional)

You can create a superuser programmatically:

```python
from sqlalchemy.orm import Session
from core.database import get_postgres_session
from crud.user import user_crud
from schemas.user import UserCreate

# Create a superuser
db = next(get_postgres_session())
superuser_data = UserCreate(
    email="admin@example.com",
    username="admin",
    password="secure_password123",
    full_name="Administrator"
)

user = user_crud.create_user(db, superuser_data)
user_crud.make_superuser(db, user.id)
user_crud.verify_user(db, user.id)
db.close()
```

## User Model Features

The User model includes the following fields:

- **Basic Info**: `id`, `email`, `username`, `full_name`
- **Authentication**: `hashed_password`, `is_active`, `is_verified`, `is_superuser`
- **Metadata**: `created_at`, `updated_at`, `last_login`
- **Profile**: `bio`, `avatar_url`
- **Settings**: `email_notifications`

## API Endpoints

### Authentication Endpoints

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Authenticate and get access token
- `GET /auth/me` - Get current user info
- `PUT /auth/me` - Update current user info
- `POST /auth/change-password` - Change user password

### Admin Endpoints (Superuser Only)

- `GET /auth/users` - List all users
- `GET /auth/users/{user_id}` - Get user by ID
- `DELETE /auth/users/{user_id}` - Delete user

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \\
     -H "Content-Type: application/json" \\
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "securepass123",
       "full_name": "Test User"
     }'
```

### 2. Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{
       "username_or_email": "testuser",
       "password": "securepass123"
     }'
```

### 3. Access Protected Endpoints

```bash
curl -X GET "http://localhost:8000/auth/me" \\
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Security Features

1. **Password Hashing**: Uses bcrypt with automatic salt generation
2. **JWT Tokens**: Signed tokens with configurable expiration
3. **Permission Levels**: Regular users, verified users, and superusers
4. **Input Validation**: Pydantic schemas validate all API inputs
5. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
6. **Token Verification**: All protected endpoints verify JWT tokens

## Database Migrations

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

## Integration with FastAPI

To integrate the authentication system with your main FastAPI app:

```python
from fastapi import FastAPI
from api.auth import router as auth_router

app = FastAPI(title="Aigis Governance API")

# Include authentication routes
app.include_router(auth_router, prefix="/api/v1")

# Use authentication dependencies in your routes
from auth.dependencies import get_current_active_user

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.username}!"}
```

## Troubleshooting

### Database Connection Issues

1. Ensure PostgreSQL is running and accessible
2. Verify database credentials in `.env` file
3. Check that the database exists
4. Ensure the user has proper permissions

### Migration Issues

1. Check Alembic configuration in `alembic.ini` and `alembic/env.py`
2. Ensure all models are imported in `alembic/env.py`
3. Verify database connection works

### Authentication Issues

1. Check that JWT secret key is properly set
2. Verify token expiration settings
3. Ensure password hashing is working correctly

## Future Enhancements

Potential improvements to consider:

1. **Email Verification**: Send verification emails for new registrations
2. **Password Reset**: Email-based password reset functionality
3. **OAuth Integration**: Support for Google, GitHub, etc.
4. **Rate Limiting**: Prevent brute force attacks
5. **Audit Logging**: Track authentication events
6. **Multi-Factor Authentication**: SMS or TOTP support
7. **Session Management**: Track and manage user sessions
