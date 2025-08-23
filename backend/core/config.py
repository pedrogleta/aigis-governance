# config.py: Manages all configuration. Using a library like pydantic for settings management is a good practice. It will load variables from the .env file.

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Application settings
    app_name: str = Field(default="Aigis Governance", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )

    # Main PostgreSQL database
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="", description="PostgreSQL password")
    postgres_db: str = Field(
        default="aigis_governance", description="PostgreSQL database name"
    )

    # SQLite database for user-created databases
    sqlite_database_path: str = Field(
        default="sample_sales.db", description="Path to SQLite database file"
    )

    # Database connection settings
    database_pool_size: int = Field(
        default=10, description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=20, description="Database max overflow connections"
    )
    database_pool_timeout: int = Field(
        default=30, description="Database connection timeout"
    )

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-here", description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time"
    )

    # API settings
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    cors_origins: list = Field(default=["*"], description="CORS allowed origins")

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        if self.postgres_password:
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        else:
            return f"postgresql://{self.postgres_user}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def sqlite_url(self) -> str:
        """Generate SQLite connection URL."""
        # Get the absolute path to the backend directory
        backend_dir = Path(__file__).parent.parent
        sqlite_path = backend_dir / self.sqlite_database_path
        return f"sqlite:///{sqlite_path}"

    # pydantic v2 style configuration
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Create global settings instance
settings = Settings()

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    settings.debug = False
elif os.getenv("ENVIRONMENT") == "development":
    settings.debug = True
