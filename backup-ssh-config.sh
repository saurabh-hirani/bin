#!/bin/bash

# Very basic script to backup ssh config because I nuked mine by mistake.
# Keeps the last 24 hour backups

curr_hour=$(date +%H)

backup_dir="$HOME/backups/ssh/$curr_hour"

if [[ -d "$backup_dir" ]]; then
  # Avoid using $backup_dir var to be paranoid because rm -rf
  rm -rf "$HOME/backups/ssh/$curr_hour"
fi

mkdir -p "$backup_dir"

cp -rpv ~/.ssh/ "$backup_dir"
