import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

__all__ = ["SessionLocal", "engine"]

load_dotenv()

db_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///memory:")

engine = create_async_engine(
    db_url,
    pool_size=20,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
)
SessionLocal = async_sessionmaker(
    expire_on_commit=False,
    class_=AsyncSession,
    bind=engine,
    autocommit=False,
    autoflush=False,
)
