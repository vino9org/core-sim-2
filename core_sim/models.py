from sqlalchemy import Integer, String
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003, VNE003
    login_name: Mapped[str] = mapped_column(String(32))
