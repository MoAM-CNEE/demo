#!/bin/bash

curr=0
for ((i=1; i<=6; i++)); do
    ((curr++))
    echo "$(date +'%Y-%m-%d %T') scaling loadtest to $curr"
    kubectl scale deploy load-test -n loadtest --replicas="$curr"
    sleep 180
done

echo "$(date +'%Y-%m-%d %T') run under max load"
sleep 240

echo "$(date +'%Y-%m-%d %T') scaling loadtest to 0"
kubectl scale deploy load-test -n loadtest --replicas=0
sleep 240
