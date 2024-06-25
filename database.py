import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

__all__ = ["SessionLocal", "engine"]

load_dotenv()

db_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///memory:")
engine = create_async_engine(db_url, echo=False)
SessionLocal = async_sessionmaker(
    expire_on_commit=False,
    class_=AsyncSession,
    bind=engine,
    autocommit=False,
    autoflush=False,
)
