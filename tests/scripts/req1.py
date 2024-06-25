import json
import sys
from datetime import datetime
from urllib import request
from uuid import uuid4


def payload(
    from_account="A834666497",
    to_account="A786432010",
    amount=15.00,
    memo="test transfer",
):
    return {
        "ref_id": uuid4().hex,
        "trx_date": datetime.now().strftime("%Y-%m-%d"),
        "debit_account_num": from_account,
        "credit_account_num": to_account,
        "currency": "USD",
        "amount": amount,
        "memo": memo,
    }


def send_api_request(url, payload):
    req = request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    with request.urlopen(req) as response:
        status_code = response.status
        response_body = json.dumps(json.loads(response.read()), indent=4)
        print(status_code)
        print(response_body)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/casa/transfers"
    send_api_request(url, payload())
