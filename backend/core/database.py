# database.py: Contains helper functions to establish and manage the database connection (e.g., using SQLAlchemy). This keeps your database logic separate and reusable.

# There will be a single main app connection to PostgreSQL but there will also be custom User Created database connections to SQLite.

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .config import settings

# Create declarative base for models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections for both PostgreSQL and SQLite."""

    def __init__(self):
        self._postgres_engine = None
        self._sqlite_engine = None
        self._postgres_session_factory = None
        self._sqlite_session_factory = None

    def _create_postgres_engine(self):
        """Create PostgreSQL engine with connection pooling."""
        if not self._postgres_engine:
            self._postgres_engine = create_engine(
                settings.postgres_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_pre_ping=True,  # Verify connections before use
                echo=settings.debug,  # Log SQL queries in debug mode
            )

            # Create session factory
            self._postgres_session_factory = sessionmaker(
                bind=self._postgres_engine,
                autocommit=False,
                autoflush=False,
            )

            # Enable foreign key support for SQLite (if using SQLite for main DB)
            if "sqlite" in settings.postgres_url:

                @event.listens_for(self._postgres_engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

    def _create_sqlite_engine(self):
        """Create SQLite engine for user-created databases."""
        if not self._sqlite_engine:
            # SQLite specific configuration
            connect_args = {
                "check_same_thread": False,  # Allow multiple threads
                "timeout": 20,  # Connection timeout
            }

            self._sqlite_engine = create_engine(
                settings.sqlite_url,
                connect_args=connect_args,
                poolclass=StaticPool,  # SQLite doesn't need connection pooling
                echo=settings.debug,
            )

            # Enable foreign key support after engine creation
            @event.listens_for(self._sqlite_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
                cursor.close()

            # Create session factory
            self._sqlite_session_factory = sessionmaker(
                bind=self._sqlite_engine,
                autocommit=False,
                autoflush=False,
            )

    @property
    def postgres_engine(self):
        """Get PostgreSQL engine, creating it if necessary."""
        if not self._postgres_engine:
            self._create_postgres_engine()
        return self._postgres_engine

    @property
    def sqlite_engine(self):
        """Get SQLite engine, creating it if necessary."""
        if not self._sqlite_engine:
            self._create_sqlite_engine()
        return self._sqlite_engine

    @property
    def postgres_session_factory(self):
        """Get PostgreSQL session factory."""
        if not self._postgres_session_factory:
            self._create_postgres_engine()
        return self._postgres_session_factory

    @property
    def sqlite_session_factory(self):
        """Get SQLite session factory."""
        if not self._sqlite_session_factory:
            self._create_sqlite_engine()
        return self._sqlite_session_factory

    def get_postgres_session(self) -> Session:
        """Get a new PostgreSQL database session."""
        session_factory = self.postgres_session_factory
        if session_factory is None:
            raise RuntimeError("PostgreSQL session factory not initialized")
        return session_factory()

    def get_sqlite_session(self) -> Session:
        """Get a new SQLite database session."""
        session_factory = self.sqlite_session_factory
        if session_factory is None:
            raise RuntimeError("SQLite session factory not initialized")
        return session_factory()

    @contextmanager
    def get_postgres_session_context(self) -> Generator[Session, None, None]:
        """Context manager for PostgreSQL database sessions."""
        session = self.get_postgres_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_sqlite_session_context(self) -> Generator[Session, None, None]:
        """Context manager for SQLite database sessions."""
        session = self.get_sqlite_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all_tables(self, engine_type: str = "postgres"):
        """Create all tables for the specified database type."""
        if engine_type == "postgres":
            Base.metadata.create_all(bind=self.postgres_engine)
        elif engine_type == "sqlite":
            Base.metadata.create_all(bind=self.sqlite_engine)
        else:
            raise ValueError("engine_type must be 'postgres' or 'sqlite'")

    def drop_all_tables(self, engine_type: str = "postgres"):
        """Drop all tables for the specified database type."""
        if engine_type == "postgres":
            Base.metadata.drop_all(bind=self.postgres_engine)
        elif engine_type == "sqlite":
            Base.metadata.drop_all(bind=self.sqlite_engine)
        else:
            raise ValueError("engine_type must be 'postgres' or 'sqlite'")

    def close_connections(self):
        """Close all database connections."""
        if self._postgres_engine:
            self._postgres_engine.dispose()
        if self._sqlite_engine:
            self._sqlite_engine.dispose()


# Create global database manager instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
def get_postgres_session() -> Session:
    """Get a new PostgreSQL database session."""
    return db_manager.get_postgres_session()


def get_sqlite_session() -> Session:
    """Get a new SQLite database session."""
    return db_manager.get_sqlite_session()


def get_postgres_engine():
    """Get PostgreSQL engine."""
    return db_manager.postgres_engine


def get_sqlite_engine():
    """Get SQLite engine."""
    return db_manager.sqlite_engine


# Context manager functions
def get_postgres_session_context():
    """Context manager for PostgreSQL database sessions."""
    return db_manager.get_postgres_session_context()


def get_sqlite_session_context():
    """Context manager for SQLite database sessions."""
    return db_manager.get_sqlite_session_context()


# Database dependency for FastAPI
def get_postgres_db() -> Generator[Session, None, None]:
    """Database dependency for FastAPI with PostgreSQL."""
    with get_postgres_session_context() as session:
        yield session


def get_sqlite_db() -> Generator[Session, None, None]:
    """Database dependency for FastAPI with SQLite."""
    with get_sqlite_session_context() as session:
        yield session
