from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import SessionLocal

from . import schemas, service

router = APIRouter(prefix="/api/casa")


# Dependency
async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@router.get("/accounts/{account_num}", response_model=schemas.AccountSchema)
async def get_account_details(account_num: str, db_session: AsyncSession = Depends(db_session)):
    account = await service.get_account_details(db_session, account_num)
    if account:
        return account

    raise HTTPException(status_code=404, detail="Account not found or inactive")


@router.post("/transfers", response_model=schemas.TransferSchema, status_code=201)
async def transfer(transfer_req: schemas.TransferSchema, session: AsyncSession = Depends(db_session)):
    try:
        return await service.transfer(session, transfer_req)
    except service.ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
