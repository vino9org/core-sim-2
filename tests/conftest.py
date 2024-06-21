import logging
import os
import sys
from datetime import datetime, timezone

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(f"{cwd}/.."))

# the following import only works after sys.path is updated
from casa import models  # noqa
from casa.api import db_session  # noqa
from main import app  # noqa


logger = logging.getLogger(__name__)


def tmp_sqlite_url():
    tmp_path = os.path.abspath(f"{cwd}/../tmp")
    os.makedirs(tmp_path, exist_ok=True)
    return f"sqlite:///{tmp_path}/test.db"


test_db_url = os.environ.get("TEST_DATABASE_URI", tmp_sqlite_url())
testing_sql_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=testing_sql_engine)


# Testing Dependency
def testing_db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# overrides default dependency injection for testing
app.dependency_overrides[db_session] = testing_db_session


@pytest.fixture(autouse=True, scope="session")
def test_db():
    """
    prepare the test database:
    1. if the database does not exist, create it
    2. run migration on the database
    3. delete the database after the test, unless KEEP_TEST_DB is set to Y
    """
    test_db_created = False

    if not database_exists(test_db_url):
        logger.info(f"==creating test database {test_db_url}")
        create_database(test_db_url)
        test_db_created = True

        # Run the migrations
        # so we set it so that alembic knows to use the correct database during testing
        os.environ["SQLALCHEMY_DATABASE_URI"] = test_db_url
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        # seed test data
        with TestingSessionLocal() as session:
            logger.info("==adding seed data")
            seed_data(session)

    # the yielded value is not used, but we need this structure to ensure the cleanup code runs
    yield testing_sql_engine

    # only delete the test database if it was created during this test run
    # to avoid accidental deletion of potentially important data
    keep_test_db = os.environ.get("KEEP_TEST_DB", "N").upper() in ["1", "Y", "YES", "TRUE"]
    if test_db_created and not keep_test_db:
        logger.info(f"==dropping test database {test_db_url}")
        drop_database(test_db_url)


@pytest.fixture(scope="session")
def session():
    with sessionmaker(autocommit=False, autoflush=False, bind=testing_sql_engine)() as session:
        yield session


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
