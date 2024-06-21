from datetime import datetime
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
    account = _get_account_(session, account_num)
    if account:
        return model2schema(account, schemas.AccountSchema)

    return None


def _get_account_(session: Session, account_num: str) -> models.Account | None:
    return (
        session.query(models.Account)
        .filter(
            and_(
                models.Account.account_num == account_num,
                models.Account.status == models.StatusEnum.ACTIVE,
            )
        )
        .first()
    )


def transfer(session: Session, transfer: schemas.TransferSchema) -> schemas.TransferSchema:
    try:
        now_dt = datetime.now()

        if transfer.ref_id is None or transfer.ref_id == "":
            transfer.ref_id = str(ulid.new())

        debit_account = _get_account_(session, transfer.debit_account_num)
        if debit_account is None:
            raise ValidationError("Invalid debit account")
        if debit_account.avail_balance < transfer.amount:
            raise ValidationError("Insufficient funds in debit account")

        credit_account = _get_account_(session, transfer.credit_account_num)
        if credit_account is None:
            raise ValidationError("Invalid credit account")

        debit_account.avail_balance -= transfer.amount
        debit_account.balance -= transfer.amount
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

        credit_account.avail_balance += transfer.amount
        credit_account.balance += transfer.amount
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

        return model2schema(transfer_obj, schemas.TransferSchema)
    except (IntegrityError, ValidationError):
        session.rollback()
        raise
