#!/usr/bin/env bash

[[ -z "$DRYRUN" ]] && DRYRUN=0

for file in $(\find . -iname *.hcl); do
  echo -n "STATUS: linting: $file: "

  if [[ "$DRYRUN" == "1" ]]; then
    output=$(diff $file <($(hclfmt $file 2>&1)))
    if [[ -n "$output" ]]; then
      echo "diff"
      echo "==================="
    else
      echo "ok"
    fi
    continue
  else
    output=$(hclfmt -w $file 2>&1)
  fi

  if [[ $? == 0 ]]; then
    echo "ok"
  else
    echo -e "error\n$output"
    echo
  fi
done
