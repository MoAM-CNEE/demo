#!/bin/bash

cd "$(dirname "$0")"

kubectl -n themis-executor port-forward svc/themis-executor-svc 31420:8080 &
sleep 10

for request_file in init/*.httpbody; do
    echo "sending $request_file"
    request_content=$(cat "$request_file")
    curl -X POST -H "Content-Type: application/json" -d "$request_content" http://localhost:31420/execute
    echo ""
done

echo "wait for SockShop to start"
sleep 180
