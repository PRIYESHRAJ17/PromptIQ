"""Database engine, session management, and lifecycle initialization."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from promptiq.core.config import settings
from promptiq.core.logging import logger

Base = declarative_base()

# Configure engine kwargs based on dialect with production connection recovery
engine_kwargs: dict = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,  # Critical for Neon / serverless postgres connection recovery after sleep
    "pool_recycle": 300,    # Recycle connections every 5 minutes to match cloud auto-suspend
}

if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings for cloud serverless environments
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Creates database tables if they do not exist."""
    # Import all models to ensure metadata is populated
    import promptiq.models  # noqa: F401

    async with engine.begin() as conn:
        logger.info("Initializing database schema...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")


async def close_db() -> None:
    """Disposes database engine connections."""
    await engine.dispose()
