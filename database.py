import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

__all__ = ["SessionLocal", "engine"]

load_dotenv()

db_url = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite+aiosqlite:///memory:")
engine = create_async_engine(db_url, echo=False)
SessionLocal = async_sessionmaker(bind=engine, autoflush=False, future=True)
