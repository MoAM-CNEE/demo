#!/bin/bash

echo "Not runnable with make run"

kubectl -n themis-executor port-forward svc/themis-executor-svc 31420:8080
