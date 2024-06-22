import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from casa.models import Account


@pytest.mark.asyncio
async def test_query_models(session: AsyncSession):
    result = await session.execute(
        select(Account).where(
            Account.account_num == "1234567890",
            Account.status == "ACTIVE",
        )
    )
    account = result.first()
    assert account.currency == "USD"
