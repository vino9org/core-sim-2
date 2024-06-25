import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(f"{cwd}/.."))

# the following import only works after sys.path is updated
from casa import models  # noqa
from casa.api import db_session  # noqa
from main import app  # noqa


logger = logging.getLogger(__name__)


# helper functions
def is_env_true(var_name: str) -> bool:
    return os.environ.get(var_name, "N").upper() in ["1", "Y", "YES", "TRUE"]


def tmp_sqlite_url():
    tmp_path = os.path.abspath(f"{cwd}/../tmp")
    os.makedirs(tmp_path, exist_ok=True)
    return f"sqlite+aiosqlite:///{tmp_path}/test.db"


def async2sync_database_uri(database_uri: str) -> str:
    """
    translate a async DATABASE_URL format string
    to a sync format, which can be used by alembic
    """
    if database_uri.startswith("sqlite+aiosqlite:"):
        return database_uri.replace("+aiosqlite", "")
    elif database_uri.startswith("postgresql+asyncpg:"):
        return database_uri.replace("+asyncpg", "+psycopg")
    else:
        return database_uri


def prep_new_test_db(test_db_url: str) -> tuple[bool, str]:
    """
    create a new test database
    run alembic schema migration
    then seed the database with some test data
    return: True if new database created
    """
    db_url = async2sync_database_uri(test_db_url)
    if database_exists(db_url):
        return False, ""

    logger.info(f"creating test database {db_url}")
    create_database(db_url)

    # Run the migrations
    # so we set it so that alembic knows to use the correct database during testing
    os.environ["ALEMBIC_DATABASE_URL"] = db_url
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # seed test data
    engine = create_engine(db_url)
    with sessionmaker(autocommit=False, autoflush=False, bind=engine)() as session:
        logger.info("adding seed data")
        seed_data(session)

    return True, db_url


# test database setup for app
# modelled after database.py in the app
test_db_url = os.environ.get("TEST_DATABASE_URL", tmp_sqlite_url())

async_testing_sql_engine = create_async_engine(test_db_url, echo=False)
AsyncTestingSessionLocal = async_sessionmaker(
    expire_on_commit=False,
    class_=AsyncSession,
    bind=async_testing_sql_engine,
)


async def testing_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncTestingSessionLocal() as session:
        yield session


# overrides default dependency injection for testing
app.dependency_overrides[db_session] = testing_db_session


# text fixtures
@pytest.fixture(autouse=True, scope="session")
def test_db():
    """
    prepare the test database:
    1. if the database does not exist, create it
    2. run migration on the database
    3. delete the database after the test, unless KEEP_TEST_DB is set to Y
    """
    test_db_created, sync_db_url = prep_new_test_db(test_db_url)

    # the yielded value is not used, but we need this structure to ensure the cleanup code runs
    yield

    # only delete the test database if it was created during this test run
    # to avoid accidental deletion of potentially important data
    if test_db_created and not is_env_true("KEEP_TEST_DB"):
        logger.info(f"dropping test database {sync_db_url}")
        drop_database(sync_db_url)


# in pytest-asyncio the default event loop is function scoped
# which causes problem with asyncpg
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session():
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        yield client


# seed database for new test database
def seed_data(session: Session):
    some_dt = datetime(2021, 1, 2, 12, 0, 1, tzinfo=timezone.utc)

    # create accounts
    account1 = models.Account(
        account_num="1234567890",
        currency="USD",
        balance=1000.00,
        avail_balance=1000.00,
        updated_at=some_dt,
    )

    account2 = models.Account(
        account_num="0987654321",
        currency="USD",
        balance=500.00,
        avail_balance=500.00,
        updated_at=some_dt,
    )

    session.add_all([account1, account2])
    session.commit()

    # create transactions
    transaction1 = models.Transaction(
        ref_id="T1234567890",
        trx_date="2021-01-01",
        currency="USD",
        amount=100.00,
        memo="Initial deposit",
        account=account1,
        created_at=some_dt,
    )

    transaction2 = models.Transaction(
        ref_id="T0987654321",
        trx_date="2021-01-01",
        currency="USD",
        amount=50.00,
        memo="Initial deposit",
        account=account2,
        created_at=some_dt,
    )

    session.add_all([transaction1, transaction2])
    session.commit()
