#!/bin/bash

kubectl get pods --all-namespaces 2>/dev/null| grep Running | awk '{ print $1, $2 }' | tr -s ' ' | while read line; do 
  ns=$(echo $line | awk '{ print $1 }')
  pod=$(echo $line | awk '{ print $2 }')
  limits=$(kubectl describe pod $pod -n $ns 2>/dev/null| grep -A2 ' Limits| Requests' | yaml2json | jq -c)
  echo "$ns: $pod: $limits"
done
