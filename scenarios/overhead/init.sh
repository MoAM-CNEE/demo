#!/bin/bash

kubectl -n themis-executor port-forward svc/themis-executor-svc 31420:8080
sleep 10
