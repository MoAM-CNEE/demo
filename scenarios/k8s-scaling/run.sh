#!/bin/bash

# shellcheck disable=SC2046
echo "$(date +'%Y-%m-%d %T') start test"

kubectl -n themis-executor port-forward svc/themis-executor-svc 31420:8080 &
cd "$(dirname "$0")"
for request_file in init/*.httpbody; do
    echo "Sending $request_file"
    request_content=$(cat "$request_file")
    curl -X POST -H "Content-Type: application/json" -d "$request_content" http://localhost:31420/execute
    echo ""
done
echo "$(date +'%Y-%m-%d %T') waiting for initialization"
sleep 180
echo "$(date +'%Y-%m-%d %T') initialized"

curr=0
for ((i=1; i<=6; i++)); do
    ((curr++))
    echo "$(date +'%Y-%m-%d %T') Scaling loadtest to $curr"
    kubectl scale deploy load-test -n loadtest --replicas="$curr"
    sleep 180
done

sleep 240

echo scaling down
kubectl scale deploy load-test -n loadtest --replicas=0
sleep 60

echo "$(date +'%Y-%m-%d %T') test finished"
