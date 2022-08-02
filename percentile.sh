#!/bin/bash
tmpfile=$(mktemp)

cat - | sort -n > "$tmpfile"
total_lines=$(wc -l "$tmpfile" | awk '{ print $1 }')

for target_percentile in $*; do
  target_line=$(echo "$target_percentile * $total_lines / 100" | bc)
  echo -n "P${target_percentile} "
  sed -n "${target_line}p" "$tmpfile"
done

rm -f "$tmpfile"
