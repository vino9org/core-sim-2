from fastapi import APIRouter, Depends, HTTPException
from psycopg import DatabaseError
from sqlalchemy.orm import Session

from database import SessionLocal

from . import schemas, service

router = APIRouter(prefix="/api/casa")


# Dependency
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/accounts/{account_num}", response_model=schemas.AccountSchema)
def get_account_details(account_num: str, db_session: Session = Depends(db_session)):
    account = service.get_account_details(db_session, account_num)
    if account:
        return account

    raise HTTPException(status_code=404, detail="Account not found or inactive")


@router.post("/transfers", response_model=schemas.TransferSchema, status_code=201)
def transfer(transfer_req: schemas.TransferSchema, session: Session = Depends(db_session)):
    try:
        return service.transfer(session, transfer_req)
    except service.ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
