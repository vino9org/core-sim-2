import logging
import os
import sys

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

logger = logging.getLogger(__name__)


cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(f"{cwd}/.."))


from core_sim.models import User  # noqa: E402


@pytest.fixture(scope="session")
def sql_engine(tmp_path_factory):
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if test_db_url is None:
        test_db_url = f"sqlite:///{tmp_path_factory.getbasetemp()}/test.db"

    if test_db_url.startswith("postgres"):
        if not test_db_url.username:
            test_db_url = test_db_url.set(username=os.environ.get("TEST_PGUSER"))
        if not test_db_url.password:
            test_db_url = test_db_url.set(password=os.environ.get("TEST_PGPASSWORD"))

    if not database_exists(test_db_url):
        logger.info(f"creating test database {test_db_url}")
        create_database(test_db_url)

    # Run the migrations
    # migrations/env.py sets the sqlalchemy.url using env var DATABASE_URL
    # so we set it so that alembic knows to use the correct database during testing
    os.environ["DATABASE_URL"] = test_db_url
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    sql_engine = create_engine(test_db_url)

    # seed test data
    with sessionmaker(bind=sql_engine)() as session:
        seed_data(session)

    yield sql_engine

    if os.environ.get("KEEP_TEST_DB", "N").upper() not in ["1", "Y", "YES", "TRUE"]:
        # drop the test database
        logger.info(f"dropping test database {test_db_url}")
        drop_database(test_db_url)


@pytest.fixture(scope="session")
def session(sql_engine):
    Session = sessionmaker(bind=sql_engine)
    session = Session()

    yield session

    session.close()


def seed_data(session):
    root = User(login_name="root")
    session.add(root)
    session.commit()
