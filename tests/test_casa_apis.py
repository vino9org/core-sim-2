from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_account_details():
    response = client.get("/api/casa/accounts/1234567890")
    assert response.status_code == 200
    assert response.json()["currency"] == "USD"


def test_get_account_not_found():
    response = client.get("/api/casa/accounts/bad_account")
    assert response.status_code == 404


def test_transfer_success():
    payload = {
        "trx_date": "2021-01-02",
        "debit_account_num": "0987654321",
        "credit_account_num": "1234567890",
        "currency": "USD",
        "amount": 15.00,
        "memo": "test transfer",
    }

    response = client.post("/api/casa/transfers", json=payload)
    assert response.status_code == 201
    assert response.json()["ref_id"] != ""


def test_transfer_with_bad_account():
    # payload with all required fields but invalid account number
    payload = {
        "trx_date": "2021-01-02",
        "debit_account_num": "0987654321",
        "credit_account_num": "bad_account",
        "currency": "USD",
        "amount": 15.00,
        "memo": "test transfer",
    }

    response = client.post("/api/casa/transfers", json=payload)
    assert response.status_code == 422


def test_transfer_invalid_request():
    # payload incomplete, trx_date is required field but not supplied
    payload = {
        "debit_account_num": "0987654321",
        "credit_account_num": "bad_account",
        "currency": "USD",
        "amount": 15.00,
        "memo": "test transfer",
    }

    response = client.post("/api/casa/transfers", json=payload)
    assert response.status_code == 422
