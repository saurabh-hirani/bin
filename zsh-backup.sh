#!/bin/bash

BACKUP_DIR="$HOME/backups/zsh-backups"
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")

# Create backups
cp "$HOME/.zshrc" "$BACKUP_DIR/.zshrc.$TIMESTAMP" 2>/dev/null
cp "$HOME/.zsh_history" "$BACKUP_DIR/.zsh_history.$TIMESTAMP" 2>/dev/null

# Remove files older than 15 days
find "$BACKUP_DIR" -name ".zshrc.*" -mtime +15 -delete
find "$BACKUP_DIR" -name ".zsh_history.*" -mtime +15 -delete
