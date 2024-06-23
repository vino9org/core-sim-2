import argparse
import csv
import os
import random
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from casa.models import Account, StatusEnum

__BALANCE_BUCKETS__ = [100.0, 500.0, 1000.0, 50000.0, 10000000.0]


load_dotenv()


def parse_command_line_options(args):
    parser = argparse.ArgumentParser(description="Generate seed data for load testing")
    parser.add_argument(
        "--truncate",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        default="load",
        help="load or gen",
    )
    parser.add_argument(
        "--source",
        dest="source",
        required=True,
    )
    parser.add_argument(
        "--batch",
        dest="batch",
        default=10000,
    )
    parser.add_argument(
        "--count",
        dest="count",
        default=10000,
    )
    parser.add_argument(
        "--start",
        dest="start",
        default=1,
    )

    options = parser.parse_args(args)
    return options


def generate_csv(file_path: str, count: int, start: int = 1):
    with open(file_path, "w") as csv_f:
        writer = csv.DictWriter(
            csv_f,
            fieldnames=["account_num", "currency", "balance"],
        )
        writer.writeheader()

        for i in _gen_random_account_num_(count, 9):
            writer.writerow(
                {
                    "account_num": f"A{i:09}",
                    "currency": "USD",
                    "balance": random.choice(__BALANCE_BUCKETS__),
                }
            )
    print(f"Generated {count} accounts in {file_path}")


def _bulk_create_accounts_(session, batch):
    now_dt = datetime.now()

    objects = [
        Account(
            account_num=row["account_num"],
            currency=row["currency"],
            balance=row["balance"],
            avail_balance=row["balance"],
            status=StatusEnum.ACTIVE,
            updated_at=now_dt,
        )
        for row in batch
    ]
    session.bulk_save_objects(objects)
    session.commit()

    return len(batch)


def _read_csv_(file_path: str, batch_size: int):
    batch = []
    with open(file_path, "r") as csv_f:
        reader = csv.DictReader(csv_f)
        for row in reader:
            batch.append(row)
            if len(batch) == batch_size:
                yield batch
                batch.clear()

        if len(batch) > 0:
            yield batch


def _truncate_tables_(session):
    session.execute(text("truncate casa_transaction cascade"))
    session.execute(text("truncate casa_account cascade"))
    session.execute(text("truncate casa_transfer"))


def _gen_random_account_num_(count: int, digits: int) -> list[int]:
    unique_numbers: set[int] = set()

    lower_bound = 10 ** (digits - 1)
    upper_bound = 10**digits - 1

    while len(unique_numbers) < count:
        number = random.randint(lower_bound, upper_bound)
        unique_numbers.add(number)

    return list(unique_numbers)


def get_sessionmaker():
    db_url = os.environ.get("ALEMBIC_DATABASE_URI")
    if not db_url:
        db_url = os.environ.get("SQLALCHEMY_DATABASE_URI")

    if not db_url:
        sys.exit("Database URL not found in environment variables")

    engine = create_engine(db_url, echo=False)
    return sessionmaker(bind=engine, autoflush=False, future=True)


if __name__ == "__main__":
    args = parse_command_line_options(sys.argv[1:])
    if args.mode == "gen":
        generate_csv(args.source, int(args.count), int(args.start))
    elif args.mode == "load":
        with get_sessionmaker()() as session:
            if args.truncate:
                _truncate_tables_(session)

            count = 0
            for batch in _read_csv_(args.source, int(args.batch)):
                count += _bulk_create_accounts_(session, batch)
                print(f"Created {count} accounts")
