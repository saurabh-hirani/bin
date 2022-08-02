#!/bin/bash

### Sample usage
# seq 1 100 | ./percentile.sh $(seq 1 10 | while read line; do echo "$line * 10" | bc; done) | termgraph
### Sample usage

tmpfile=$(mktemp)

cat - | sort -n > "$tmpfile"
total_lines=$(wc -l "$tmpfile" | awk '{ print $1 }')

for target_percentile in $*; do
  target_line=$(echo "$target_percentile * $total_lines / 100" | bc)
  echo -n "P${target_percentile} "
  sed -n "${target_line}p" "$tmpfile"
done

rm -f "$tmpfile"
