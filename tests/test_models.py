from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from casa.models import Account, StatusEnum


async def test_query_models(session: AsyncSession):
    account = (
        (
            await session.execute(
                select(Account)
                .where(
                    Account.account_num == "1234567890",
                    Account.status == StatusEnum.ACTIVE,
                )
                .options(selectinload(Account.transactions))
            )
        )
        .scalars()
        .first()
    )

    assert account
    assert account.currency == "USD"
    assert len(account.transactions) >= 1
