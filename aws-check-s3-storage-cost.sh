#!/bin/bash

set -eou pipefail

# ./check-s3-storage-cost.sh [bucket]

# List of buckets or default to all buckets
buckets=${1:-$(aws s3api list-buckets --query "Buckets[].Name" --output text)}

RUN_PARALLEL=${RUN_PARALLEL:-0}
PER_GB_STORAGE_COST=${PER_GB_STORAGE_COST:-0.026}

# This function assumes that storage < 50 TB.
# S3 standard storage tier cost changes per GB post this.
find_storage_cost() {
  size="$1"
  echo "scale=2; $(echo "scale=2; $size / (1024 * 1024 * 1024)" | bc) * $PER_GB_STORAGE_COST" | bc
}

find_bucket_size_contents() {
  bucket="$1"

  # Get the size and count of objects in the bucket
  set +e
  bucket_size_contents=$(aws s3api list-objects --bucket "$bucket" --output json --query "[sum(Contents[].Size), length(Contents[])]" 2> /dev/null)
  # shellcheck disable=2181
  if [[ $? -ne 0 ]]; then
    echo >&2 "WARN: $bucket: failed to get bucket size and object count"
    echo "$bucket,0,0"
    return 0
  fi
  set -e

  # Parse the output
  size=$(echo "$bucket_size_contents" | jq -r '.[0] // 0')
  count=$(echo "$bucket_size_contents" | jq -r '.[1] // 0')

  # Check if bucket is empty
  if [[ "$count" -eq 0 ]]; then
    echo >&2 "STATUS: Skipping empty bucket $bucket"
    return
  fi

  storage_cost=$(find_storage_cost "$size")

  # Output the bucket information
  echo "$bucket,$size,$count,$storage_cost"
}

for bucket in $buckets; do
  echo >&2 "STATUS: $bucket: checking bucket size and object count"
  if [[ "$RUN_PARALLEL" == "1" ]]; then
    find_bucket_size_contents "$bucket" &
  else
    find_bucket_size_contents "$bucket"
  fi
done

if [[ "$RUN_PARALLEL" == "1" ]]; then
  wait
fi
