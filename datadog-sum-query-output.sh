#!/bin/bash

## Sample usage
# echo "dd_query" | ./datadog-run-queries.sh '15:41:00' '15:42:00' - | ./datadog-sum-query-output.sh -
## Sample usage

cat $1 | jq '.series[].pointlist[][1]' | paste -sd+ | bc
