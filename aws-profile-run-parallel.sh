#!/bin/bash

# inspired by https://twitter.com/arjunmahishi/status/1434781043358265348
\grep '\[' ~/.aws/credentials | sed 's/\[//g;s/\]//g;' | parallel -P $(lscpu | \grep -P '^CPU\(s\)' | awk '{ print $2 }') "echo {} && mkdir -p /var/tmp/aws/{} && aws $2 --profile {} > /var/tmp/aws/{}/$1.json 2>&1"
