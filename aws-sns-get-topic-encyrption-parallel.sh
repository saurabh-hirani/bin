#!/bin/bash

cust_func(){
  aws sns get-topic-attributes --topic-arn $2 --query 'Attributes.KmsMasterKeyId' | grep -v null > /var/tmp/sns/topic-encryption-status/$1.txt 2>&1
}

target_topic=$1
mkdir -p /var/tmp/sns/topic-encryption-status

while IFS= read -r topic_arn; do
  topic_name=$(echo "$topic_arn" | awk -F ':' '{ print $NF }')
  if ! [[ -z "$target_topic" ]]; then
    if [[ "$topic_name" != "$target_topic" ]]; then
      echo "Skipping: $topic_name"
      continue
    fi
  fi
  echo "Checking: $topic_name"
  cust_func "$topic_name" "$topic_arn" &
done < /var/tmp/sns-topic-arns.txt

wait
echo "All topics done."
