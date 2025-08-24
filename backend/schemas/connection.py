from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UserConnectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    db_type: str = Field(..., description="Database type, e.g., 'sqlite' or 'postgres'")
    host: Optional[str] = Field(None, description="Host for DB or file path for SQLite")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port for DB")
    username: Optional[str] = Field(None)
    database_name: Optional[str] = Field(None)


class UserConnectionCreate(UserConnectionBase):
    password: Optional[str] = Field(None, description="Password for database user")


class UserConnectionResponse(UserConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
