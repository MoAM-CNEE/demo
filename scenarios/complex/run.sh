#!/bin/bash

sleep 1200
source $MGR_KOD/ii-executor-openrc.sh

PREFIX="stress-test-"
openstack server list -f value -c ID -c Name | while read -r id name; do
  if [[ $name == $PREFIX* ]]; then
    created=$(openstack server show "$id" -f value -c created)
    echo "$name | $created"
  fi
done
