#!/bin/bash

sort -nr | uniq -c | sort -nr -k1 | awk '{ print $2, $1 }' | termgraph
