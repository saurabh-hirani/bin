#!/bin/bash

# $0 $url $parallel_req $sleep_time_between_each_batch

target_url=$1
parallel_req_count=$2
sleep_time=${3:-0}

echo "STATUS: $(date) target_url=$target_url parallel_req_count=$parallel_req_count sleep=${sleep_time}s" >&2
echo

call_url(){
  curl -I --connect-timeout 5 "$target_url" 2>/dev/null | grep HTTP
}

start_time=$(date +%s)
total_requests=0
while : ; do
  echo -n "$target_url: "
  count=0
  while [[ $count -lt $parallel_req_count ]]; do
    call_url &
    total_requests=$((total_requests + 1))
    count=$((count + 1))
  done
  wait

  sleep $sleep_time

  now_time=$(date +%s)
  total_time=$(echo "($now_time - $start_time)" | bc)
  rps=$(echo "scale=2; $total_requests / $total_time" | bc)
  rpm=$(echo "scale=2; $rps * 60" | bc)
  echo "$(date): total_time=${total_time}s total_requests=$total_requests rps=${rps} rpm=${rpm}"

  echo
done
