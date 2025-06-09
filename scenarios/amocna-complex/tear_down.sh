#!/bin/bash

kubectl -n themis-executor port-forward svc/themis-executor-svc 31420:8080 &
sleep 10

curl -X POST http://localhost:31420/execute \
  -H "Content-Type: application/json" \
  -d '{
    "collectionName": "openstack",
    "actionName": "DeleteInstanceAction",
    "params": {
      "region": "RegionOne",
      "namePattern": "stress-test-.*"
    }
  }'
echo ""
