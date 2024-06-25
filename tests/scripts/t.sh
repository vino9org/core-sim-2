#!/bin/bash

URL=$1

if [ "$HOST" == "" ]; then
    URL="http://localhost:8000/api/casa/transfers"
fi

curl -v -XPOST $URL -H "Content-Type: application/json" -d @request1.json | jq .
