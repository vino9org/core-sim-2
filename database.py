import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

__all__ = ["SessionLocal", "engine"]

load_dotenv()

db_url = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
conn_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=conn_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
