import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

__all__ = ["SessionLocal", "engine"]

load_dotenv()
db_url = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
conn_args = {}

if db_url.startswith("sqlite"):
    conn_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=conn_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
