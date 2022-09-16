#!/bin/bash

kubectl get pods --all-namespaces 2>/dev/null| grep Running | awk '{ print $1, $2 }' | tr -s ' ' | while read line; do
  ns=$(echo $line | awk '{ print $1 }')
  pod=$(echo $line | awk '{ print $2 }')
  limits=$(kubectl describe pod "$pod" -n "$ns" 2>/dev/null | \grep -A10 ' Limits' | \grep -P 'cpu:|memory:' | head -2 | tr -d ' ' | tr '\n' ',')
  [[ -z "$limits" ]] && limits="na"
  requests=$(kubectl describe pod "$pod" -n "$ns" 2>/dev/null | \grep -A10 ' Requests' | \grep -P 'cpu:|memory:' | head -2 | tr -d ' ' | tr '\n' ',')
  [[ -z "$requests" ]] && requests="na"
  echo "ns=$ns pod=$pod limits=$limits requests=$requests"
done
