#!/bin/bash

grep '\[' ~/.aws/credentials | sed 's/\[//g;s/\]//g;' | parallel -P 8 "echo {} && mkdir -p /var/tmp/aws/{} && aws $2 --profile {} > /var/tmp/aws/{}/$1.json 2>&1"
