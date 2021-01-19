#!/bin/bash

cust_func(){
  aws kinesis list-tags-for-stream --stream-name $1 > /var/tmp/kinesis/stream-tags/$1.json 2>&1
}

target_stream=$1
mkdir -p /var/tmp/kinesis/stream-tags

while IFS= read -r stream_name; do
  if ! [[ -z "$target_stream" ]]; then
    if [[ "$stream_name" != "$target_stream" ]]; then
      echo "Skipping: $stream_name"
      continue
    fi
  fi
  echo "Checking: $stream_name"
  cust_func "$stream_name" &
done < /var/tmp/kinsis-streams.txt

wait
echo "All streams done."
