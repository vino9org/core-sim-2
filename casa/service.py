import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Type, TypeVar

import ulid
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas

__ALL__ = ["ValidationError", "get_account_details", "transfer"]

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


def model2schema(model_obj: Any, schema_cls: Type[T]) -> T:
    return schema_cls.model_validate(model_obj)


async def get_account_details(session: AsyncSession, account_num: str) -> schemas.AccountSchema | None:
    stmt = select(models.Account).filter(
        models.Account.account_num == account_num,
        models.Account.status == models.StatusEnum.ACTIVE,
    )
    result = await session.execute(stmt)
    account = result.scalars().first()

    if account:
        return model2schema(account, schemas.AccountSchema)

    return None


async def _lock_accounts_for_trasnfer_(
    session: AsyncSession,
    debit_account_num: str,
    credit_account_num: str,
) -> tuple[models.Account, models.Account]:
    stmt = (
        select(models.Account)
        .filter(
            models.Account.account_num.in_([debit_account_num, credit_account_num]),
            models.Account.status == models.StatusEnum.ACTIVE,
        )
        .with_for_update()
    )
    result = await session.execute(stmt)
    accounts = result.scalars().all()

    if len(accounts) != 2:
        await session.rollback()
        raise ValidationError("Invalid debit or credit account number")

    if accounts[0].account_num == debit_account_num:
        return accounts[0], accounts[1]
    else:
        return accounts[1], accounts[0]


async def transfer(
    session: AsyncSession, transfer: schemas.TransferSchema
) -> tuple[schemas.TransferSchema, list[tuple[Type[models.Transaction], int]]]:
    """
    perform a transfer and returns:
    1. transfer object
    2. list of Transfer objects and their id (to be used to event publishing later)
    """
    try:
        now_dt = datetime.now()
        transfer_amount = Decimal(transfer.amount)

        if transfer.ref_id is None or transfer.ref_id == "":
            transfer.ref_id = str(ulid.new())

        debit_account, credit_account = await _lock_accounts_for_trasnfer_(
            session,
            transfer.debit_account_num,
            transfer.credit_account_num,
        )
        if debit_account.avail_balance < transfer.amount:
            raise ValidationError("Insufficient funds in debit account")

        debit_account_balance = debit_account.balance - transfer_amount
        debit_account.avail_balance = debit_account_balance
        debit_account.balance = debit_account_balance

        debit_transction = models.Transaction(
            ref_id=transfer.ref_id,
            trx_date=transfer.trx_date,
            currency=transfer.currency,
            amount=-transfer.amount,
            memo=transfer.memo,
            account=debit_account,
            created_at=now_dt,
            running_balance=debit_account_balance,
        )

        credit_account_balance = credit_account.balance + transfer_amount
        credit_account.avail_balance = credit_account_balance
        credit_account.balance = credit_account_balance

        credit_transction = models.Transaction(
            ref_id=transfer.ref_id,
            trx_date=transfer.trx_date,
            currency=transfer.currency,
            amount=transfer.amount,
            memo=f"from {transfer.debit_account_num}: {transfer.memo}",
            account=credit_account,
            created_at=now_dt,
            running_balance=credit_account_balance,
        )

        transfer_obj = models.Transfer(
            ref_id=transfer.ref_id,
            trx_date=transfer.trx_date,
            currency=transfer.currency,
            amount=transfer.amount,
            memo=transfer.memo,
            debit_account_num=transfer.debit_account_num,
            credit_account_num=transfer.credit_account_num,
            created_at=now_dt,
        )

        session.add_all([debit_account, credit_account, debit_transction, credit_transction, transfer_obj])
        await session.commit()

        events = [
            (models.Transaction, debit_transction.id),
            (models.Transaction, credit_transction.id),
        ]
        schema = model2schema(transfer_obj, schemas.TransferSchema)

        return schema, events

    except (IntegrityError, ValidationError):
        await session.rollback()
        raise


def publish_events(events: list[tuple[Type[models.BaseT], int]]) -> int:
    for e in events:
        msg = f"publishing event for {e[0].__name__}({e[1]})"
        logger.info(msg)
    return 0
