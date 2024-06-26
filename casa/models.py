import enum
from datetime import datetime
from decimal import Decimal
from typing import List, TypeVar

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


BaseT = TypeVar("BaseT", bound=Base)


class StatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class Account(Base):
    __tablename__ = "casa_account"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_num: Mapped[str] = mapped_column(String(32), unique=False)
    currency: Mapped[str] = mapped_column(String(3))
    balance: Mapped[Decimal] = mapped_column(DECIMAL(14, 2))
    avail_balance: Mapped[Decimal] = mapped_column(DECIMAL(14, 2))
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account")

    __table_args__ = (Index("account_status_idx", "account_num", "status", unique=True),)


class Transaction(Base):
    __tablename__ = "casa_transaction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trx_date: Mapped[str] = mapped_column(String(10), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(14, 2))
    running_balance: Mapped[Decimal] = mapped_column(DECIMAL(14, 2))
    ref_id: Mapped[str] = mapped_column(String(32))
    trx_id: Mapped[str] = mapped_column(String(32))
    memo: Mapped[str] = mapped_column(String(100))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("casa_account.id"))
    account: Mapped[Account] = relationship("Account", back_populates="transactions")

    __table_args__ = (Index("account_date_idx", "account_id", "trx_date"),)


class Transfer(Base):
    __tablename__ = "casa_transfer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trx_id: Mapped[str] = mapped_column(String(32), unique=True)
    trx_date: Mapped[str] = mapped_column(String(10), index=True)
    ref_id: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(14, 2))
    memo: Mapped[str] = mapped_column(String(100))
    debit_account_num: Mapped[str] = mapped_column(String(32))
    credit_account_num: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
