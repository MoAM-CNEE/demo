#!/bin/bash

kubectl scale deploy load-test -n loadtest --replicas=0
#cd "$(dirname "$0")"
#kubectl delete -f manifests/init
# TODO: delete * request
