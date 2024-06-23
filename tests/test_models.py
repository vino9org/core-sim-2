from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from casa.models import Account, StatusEnum


def test_query_models(session: Session):
    account = (
        session.execute(
            select(Account)
            .where(
                Account.account_num == "1234567890",
                Account.status == StatusEnum.ACTIVE,
            )
            .options(selectinload(Account.transactions))
        )
        .scalars()
        .first()
    )
    assert account
    assert account.currency == "USD"
