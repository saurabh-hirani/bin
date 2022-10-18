#!/bin/bash

# Very basic script to backup zsh configs
# Keeps the last 24 hour backups

curr_hour=$(date +%H)

backup_dir="$HOME/backups/zshrc/$curr_hour"

if [[ -d "$backup_dir" ]]; then
  # Avoid using $backup_dir var to be paranoid because rm -rf
  rm -rf "$HOME/backups/zshrc/$curr_hour"
fi

mkdir -p "$backup_dir"

cp -rpv ~/.oh-my-zsh/ "$backup_dir"
cp -rpv ~/.zshrc "$backup_dir"
