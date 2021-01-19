#!/bin/bash

cust_func(){
  aws s3api get-bucket-acl --bucket $1 > /var/tmp/s3/buckets/get-bucket-acl/$1.json 2>&1
}

while IFS= read -r bucket_name; do
  echo "$bucket_name"
  cust_func "$bucket_name" &
done < /var/tmp/buckets.txt

wait
echo "All buckets done."
