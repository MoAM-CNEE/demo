#!/bin/bash

NAMESPACE="loadtest"
DEPLOYMENT="load-test"
SLEEP_DURATION_S=300

scale() {
    local replicas=$1
    echo "$(date +'%Y-%m-%d %T') scaling $DEPLOYMENT to $replicas"
    kubectl scale deploy "$DEPLOYMENT" -n "$NAMESPACE" --replicas="$replicas"
    sleep "$SLEEP_DURATION_S"
}

for replicas in {1..6}; do
    scale "$replicas"
done

for replicas in 3 1 0; do
    scale "$replicas"
done
