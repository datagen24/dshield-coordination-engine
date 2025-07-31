"""Database connection management for DShield Coordination Engine."""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from services.api.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_pre_ping=True,  # Enable connection health checks
    echo=settings.debug,  # Enable SQL logging in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite for development)."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries for performance monitoring."""
    conn.info.setdefault("query_start_time", []).append(
        conn.info.get("query_start_time", 0)
    )


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time."""
    total = conn.info.get("query_start_time", 0)
    if total > 1.0:  # Log queries taking more than 1 second
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")


def get_database_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup.

    Yields:
        Session: SQLAlchemy database session

    Example:
        with get_database_session() as session:
            result = session.query(AnalysisSession).all()
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_database_session_context() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Returns:
        Session: SQLAlchemy database session

    Example:
        with get_database_session_context() as session:
            result = session.query(AnalysisSession).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


async def check_database_health() -> dict[str, str]:
    """Check database connection health.

    Returns:
        dict: Health status with details
    """
    try:
        with get_database_session_context() as session:
            # Execute a simple query to test connection
            session.execute("SELECT 1")
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
        }


def get_engine_info() -> dict[str, any]:
    """Get database engine information for monitoring.

    Returns:
        dict: Engine configuration and statistics
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
        "url": str(engine.url).replace(engine.url.password, "***")
        if engine.url.password
        else str(engine.url),
    }
