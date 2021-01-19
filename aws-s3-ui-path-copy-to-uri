#!/bin/bash

echo -n "s3://"
cat - | grep -v 'Amazon S3' | tr -d ' ' | grep -v '^$' | while read token; do
  if echo $token | grep -qs '/'; then
    echo -n "$token"
  else
    echo -n "$token/"
  fi
done
echo
