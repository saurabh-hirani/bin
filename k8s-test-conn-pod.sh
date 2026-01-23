#!/bin/bash
kubectl run test-connectivity -n $1 --rm -it --image=curlimages/curl -- sh
