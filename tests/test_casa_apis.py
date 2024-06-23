async def test_get_account_details(client):
    response = await client.get("/api/casa/accounts/1234567890")
    assert response.status_code == 200
    assert response.json()["currency"] == "USD"


async def test_get_account_not_found(client):
    response = await client.get("/api/casa/accounts/bad_account")
    assert response.status_code == 404


async def test_transfer_success(client):
    payload = {
        "trx_date": "2021-01-02",
        "debit_account_num": "0987654321",
        "credit_account_num": "1234567890",
        "currency": "USD",
        "amount": 15.00,
        "memo": "test transfer",
    }

    response = await client.post("/api/casa/transfers", json=payload)
    assert response.status_code == 201
    assert response.json()["ref_id"] != ""


async def test_transfer_with_bad_account(client):
    # payload with all required fields but invalid account number
    payload = {
        "trx_date": "2021-01-02",
        "debit_account_num": "0987654321",
        "credit_account_num": "bad_account",
        "currency": "USD",
        "amount": 15.00,
        "memo": "test transfer",
    }

    response = await client.post("/api/casa/transfers", json=payload)
    assert response.status_code == 422


async def test_transfer_invalid_request(client):
    # payload incomplete, trx_date is required field but not supplied
    payload = {
        "debit_account_num": "0987654321",
        "credit_account_num": "bad_account",
        "currency": "USD",
        "amount": 15.00,
        "memo": "test transfer",
    }

    response = await client.post("/api/casa/transfers", json=payload)
    assert response.status_code == 422
