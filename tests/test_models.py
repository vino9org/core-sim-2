from casa.models import Account, StatusEnum


def test_query_models(session):
    account = session.query(Account).filter_by(account_num="1234567890", status=StatusEnum.ACTIVE).first()
    assert account.currency == "USD"
