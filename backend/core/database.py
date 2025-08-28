# database.py: Contains helper functions to establish and manage the database connection (e.g., using SQLAlchemy). This keeps your database logic separate and reusable.

# There will be a single main app connection to PostgreSQL but there will also be custom User Created database connections to SQLite.

from typing import Generator, Dict, Tuple, Any
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .config import settings
from .tenancy import MAX_IDENTIFIER_LEN

# Create declarative base for models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections for both PostgreSQL and SQLite."""

    def __init__(self):
        self._postgres_engine = None
        self._sqlite_engine = None
        self._postgres_session_factory = None
        self._sqlite_session_factory = None
        # cache of user connection engines keyed by (user_id, connection_id)
        self._user_connection_engines: Dict[Tuple[int, int], Any] = {}
        self._user_connection_session_factories: Dict[
            Tuple[int, int], sessionmaker
        ] = {}

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
        # dispose user connection engines
        for engine in self._user_connection_engines.values():
            try:
                engine.dispose()
            except Exception:
                pass
        self._user_connection_engines.clear()
        self._user_connection_session_factories.clear()

    # --- User connection dynamic engines ---
    def get_user_connection_engine(
        self,
        user_id: int,
        connection_id: int,
        db_type: str,
        host: str | None,
        port: int | None,
        username: str | None,
        password: str | None,
        database_name: str | None,
    ):
        key = (user_id, connection_id)
        if key in self._user_connection_engines:
            return self._user_connection_engines[key]

        if db_type.lower() == "sqlite":
            # host is file path
            url = f"sqlite:///{host}"
            engine = create_engine(
                url,
                connect_args={"check_same_thread": False, "timeout": 20},
                poolclass=StaticPool,
                echo=settings.debug,
            )

            @event.listens_for(engine, "connect")
            def _sqlite_fk(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()
        elif db_type.lower() in ("postgres", "postgresql"):
            # Build postgres URL
            auth = (
                f"{username}:{password}@"
                if username and password
                else f"{username}@"
                if username
                else ""
            )
            port_part = f":{port}" if port else ""
            url = f"postgresql://{auth}{host}{port_part}/{database_name}"
            engine = create_engine(
                url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_pre_ping=True,
                echo=settings.debug,
            )
        elif db_type.lower() == "custom":
            # Custom connection points to the main Postgres DB but targets a specific schema.
            # We use settings.postgres_url and set search_path to the provided schema name via database_name.
            # database_name expected to be the schema name for this custom connection.
            schema_name = (database_name or "").strip()
            if not schema_name:
                raise ValueError(
                    "Custom connection requires schema name in database_name"
                )
            engine = create_engine(
                settings.postgres_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_pre_ping=True,
                echo=settings.debug,
            )

            @event.listens_for(engine, "connect")
            def _set_search_path(dbapi_connection, connection_record):
                try:
                    cursor = dbapi_connection.cursor()
                    # Quote identifier safely by simple replacement (schema is sanitized at creation time)
                    # Avoid exceeding identifier length
                    safe_schema = schema_name[:MAX_IDENTIFIER_LEN]
                    cursor.execute(f'SET search_path TO "{safe_schema}"')
                    cursor.close()
                except Exception:
                    # If setting search_path fails, proceed without raising to avoid breaking connection creation
                    try:
                        cursor.close()
                    except Exception:
                        pass
        else:
            raise ValueError("Unsupported db_type")

        self._user_connection_engines[key] = engine
        self._user_connection_session_factories[key] = sessionmaker(
            bind=engine, autocommit=False, autoflush=False
        )
        return engine

    def get_user_connection_session(self, user_id: int, connection_id: int):
        key = (user_id, connection_id)
        factory = self._user_connection_session_factories.get(key)
        if factory is None:
            raise RuntimeError("User connection session factory not initialized")
        return factory()


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
