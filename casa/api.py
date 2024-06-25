import logging
from typing import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import SessionLocal

from . import schemas, service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/casa")


# Dependency
async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@router.get("/accounts/{account_num}", response_model=schemas.AccountSchema)
async def get_account_details(
    account_num: str,
    db_session: AsyncSession = Depends(db_session),
):
    account = await service.get_account_details(db_session, account_num)
    if account:
        return account

    raise HTTPException(status_code=404, detail="Account not found or inactive")


@router.post("/transfers", response_model=schemas.TransferSchema, status_code=201)
async def transfer(
    transfer_req: schemas.TransferSchema,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
):
    try:
        result, transactions = await service.transfer(session, transfer_req)
        background_tasks.add_task(service.publish_events, transactions)
        logger.info(f"processed request: {result.ref_id}")
        return result
    except service.ValidationError as e:
        logger.info(f"request failed validation: {transfer_req.ref_id}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"An error occured: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
