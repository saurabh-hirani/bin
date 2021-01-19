#!/bin/bash

cust_func(){
  aws sqs list-queue-tags --queue-url $2 > /var/tmp/sqs/queue-tags/$1.txt 2>&1
}

target_queue=$1
mkdir -p /var/tmp/sqs/queue-tags

while IFS= read -r queue_url; do
  queue_name=$(echo "$queue_url" | xargs basename)
  if ! [[ -z "$target_queue" ]]; then
    if [[ "$queue_name" != "$target_queue" ]]; then
      echo "Skipping: $queue_name"
      continue
    fi
  fi
  echo "Checking: $queue_name"
  cust_func "$queue_name" "$queue_url" &
done < /var/tmp/sqs-queue-urls.txt

wait
echo "All queues done."
