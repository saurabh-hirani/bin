#!/bin/bash

### Sample usage
# for i in $(seq 1 10); do shuf -i 1-10 -n 1; done | termgraph-it.sh
### Sample usage

sort -nr | uniq -c | sort -nr -k1 | awk '{ print $2, $1 }' | termgraph
