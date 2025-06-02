#!/bin/bash

kubectl scale deploy load-test -n loadtest --replicas=0

kubectl -n themis-executor port-forward svc/themis-executor-svc 31420:8080 &
sleep 2

curl -X POST http://localhost:31420/execute \
  -H "Content-Type: application/json" \
  -d '{
    "collectionName": "moam.statemanager",
    "actionName": "DeleteEntityAction",
    "params": {
      "query": "select * from entity"
    }
  }'
echo ""
