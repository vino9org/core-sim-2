from datetime import datetime
from typing import Annotated, Optional, TypeAlias

from annotated_types import Gt
from pydantic import BaseModel, constr

positive: TypeAlias = Annotated[float, Gt(0)]
curreny: TypeAlias = Annotated[str, constr(min_length=3, max_length=3)]


class AccountSchema(BaseModel):
    account_num: str
    currency: curreny
    balance: float
    avail_balance: float
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class TransferSchema(BaseModel):
    ref_id: Optional[str] = None
    trx_date: str
    debit_account_num: str
    credit_account_num: str
    currency: curreny
    amount: positive
    memo: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
