#!/bin/bash

usage="$0 prometheus_conn_str queries_file|- time_range"

# Sample
# echo -e "valid_prometheus_query" | ./prometheus-run-queries.sh http://localhost:9090/ - '5 minutes ago'
# ./prometheus-run-queries.sh http://localhost:9090/ /var/tmp/queries.txt '5 minutes ago'


if [[ $# -ne 3 ]]; then
  echo "ERROR: Invalid usage"
  echo "$usage"
  exit 1
fi

prometheus_conn_str="$1"
queries_file="$2"
time_range="$3"

start_time=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z" -d "$time_range") && end_time=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

cat "$queries_file" | grep -v '#' | while read -r query; do
  echo "==============="
  echo "running: $query"
  encoded_query=$(echo "$query" | jq -SRr @uri)
  curl -s "$prometheus_conn_str/api/v1/query_range?start=$start_time&end=$end_time&step=60s&query=$encoded_query" | jq
  echo "==============="
done
