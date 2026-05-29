from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool.impl import NullPool
from app.config.env_config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = settings.DATABASE_URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_async_engine(DATABASE_URL, future=True)
test_engine = create_async_engine(TEST_DATABASE_URL, future=True,poolclass=NullPool)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Ensure commit for any pending changes
        except Exception:
            await session.rollback()  # Rollback on error
            raise



# Transaction helper
@asynccontextmanager
async def get_transaction_session(async_session_factory):
    session: AsyncSession = async_session_factory()
    try:
        async with session.begin():
            yield session
    except Exception as e:
        logger.error(f"Error in transaction: {e}")
        await session.rollback()  # Rollback on error
        raise
    finally:
        await session.close()