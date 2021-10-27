#!/bin/bash

## Sample usage
# echo "dd_query" | ./datadog-run-queries.sh '15:41:00' '15:42:00' -
# echo "dd_query" | TIME_RANGE='10 minutes ago' ./datadog-run-queries.sh '' '' -
## Sample usage

usage="DD_API_KEY=xxxx DD_APP_KEY=xxx $0 start_time_local_hh_mm_ss end_time_local_hh_mm_ss queries_file"

if [[ $# -ne 3 ]]; then
  echo "ERROR: Invalid usage"
  echo "$usage"
  exit 1
fi

if ! command -v local-time-to-utc > /dev/null; then
  echo "ERROR: local-time-to-utc command not found. Clone from saurabh-hirani/bin repo."
  exit 1
fi

if [[ -z $DD_API_KEY ]]; then
  echo "ERROR: DD_API_KEY not set"
  echo "$usage"
  exit 1
fi

if [[ -z $DD_APP_KEY ]]; then
  echo "ERROR: DD_APP_KEY not set"
  echo "$usage"
  exit 1
fi

start_time="$1"
end_time="$2"
queries_file="$3"

if [[ -n $TIME_RANGE ]]; then
  export start_time_epoch=$(date -u +%s -d "$TIME_RANGE")
  export end_time_epoch=$(date -u +%s)
else
  export start_time_epoch=$(local-time-to-utc $start_time '%s')
  export end_time_epoch=$(local-time-to-utc $end_time '%s')
fi

cat "$queries_file" | grep -v '#' | while read -r query; do
  encoded_query=$(echo "$query" | jq -SRr @uri)
  set -x
  curl -X GET "https://api.datadoghq.com/api/v1/query?from=$start_time_epoch&to=$end_time_epoch&query=$encoded_query" -H "Content-Type: application/json" -H "DD-API-KEY: $DD_API_KEY" -H "DD-APPLICATION-KEY: $DD_APP_KEY" | jq
done
