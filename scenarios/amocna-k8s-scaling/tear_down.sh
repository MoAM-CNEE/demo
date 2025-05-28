#!/bin/bash

kubectl scale deploy load-test -n loadtest --replicas=0
