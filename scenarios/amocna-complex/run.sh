#!/bin/bash

echo "$(date +'%Y-%m-%d %T') wait for rule trigger"
sleep 900
source $MGR_KOD/ii-executor-openrc.sh

echo "$(date +'%Y-%m-%d %T') get creation times"
PREFIX="stress-test-"
openstack server list -f value -c ID -c Name | while read -r id name; do
  if [[ $name == $PREFIX* ]]; then
    created=$(openstack server show "$id" -f value -c created)
    echo "$name | $created"
  fi
done
