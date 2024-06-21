from datetime import datetime
from decimal import Decimal
from typing import Any, Type, TypeVar

import ulid
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas

T = TypeVar("T", bound=BaseModel)


class ValidationError(Exception):
    pass


def model2schema(model_obj: Any, schema_cls: Type[T]) -> T:
    return schema_cls.model_validate(model_obj)


def get_account_details(session: Session, account_num: str) -> schemas.AccountSchema | None:
    account = (
        session.query(models.Account)
        .filter(
            and_(
                models.Account.account_num == account_num,
                models.Account.status == models.StatusEnum.ACTIVE,
            )
        )
        .first()
    )

    if account:
        return model2schema(account, schemas.AccountSchema)

    return None


def _lock_accounts_for_trasnfer_(
    session: Session,
    debit_account_num: str,
    credit_account_num: str,
) -> tuple[models.Account, models.Account]:
    accounts = (
        session.query(models.Account)
        .filter(
            models.Account.account_num.in_([debit_account_num, credit_account_num]),
            models.Account.status == models.StatusEnum.ACTIVE,
        )
        .with_for_update()
        .all()
    )

    if len(accounts) != 2:
        session.rollback()
        raise ValidationError("Invalid debit or credit account number")

    if accounts[0].account_num == debit_account_num:
        return accounts[0], accounts[1]
    else:
        return accounts[1], accounts[0]


def transfer(session: Session, transfer: schemas.TransferSchema) -> schemas.TransferSchema:
    try:
        now_dt = datetime.now()
        transfer_amount = Decimal(transfer.amount)

        if transfer.ref_id is None or transfer.ref_id == "":
            transfer.ref_id = str(ulid.new())

        debit_account, credit_account = _lock_accounts_for_trasnfer_(
            session,
            transfer.debit_account_num,
            transfer.credit_account_num,
        )
        if debit_account.avail_balance < transfer.amount:
            raise ValidationError("Insufficient funds in debit account")

        debit_account.avail_balance -= Decimal(transfer.amount)
        debit_account.balance -= transfer_amount
        session.add(debit_account)

        session.add(
            models.Transaction(
                ref_id=transfer.ref_id,
                trx_date=transfer.trx_date,
                currency=transfer.currency,
                amount=-transfer.amount,
                memo=transfer.memo,
                account=debit_account,
                created_at=now_dt,
            )
        )

        credit_account.avail_balance += transfer_amount
        credit_account.balance += transfer_amount
        session.add(credit_account)

        session.add(
            models.Transaction(
                ref_id=transfer.ref_id,
                trx_date=transfer.trx_date,
                currency=transfer.currency,
                amount=transfer.amount,
                memo=f"from {transfer.debit_account_num}: {transfer.memo}",
                account=credit_account,
                created_at=now_dt,
            )
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
        session.add(transfer_obj)
        session.commit()

        transfer.created_at = now_dt
        return transfer

        # this actually triggers a query in the database, why?!
        # return model2schema(transfer_obj, schemas.TransferSchema)

    except (IntegrityError, ValidationError):
        session.rollback()
        raise
