#!/bin/bash

kubectl delete namespace scenario-k8s-scaling
kubectl scale deploy load-test -n loadtest --replicas=0
