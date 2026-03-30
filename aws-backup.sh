#!/bin/bash

BACKUP_DIR="$HOME/backups/aws-backups"
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")

mkdir -p "$BACKUP_DIR/$TIMESTAMP"

# Backup entire .aws directory
rsync -a "$HOME/.aws/" "$BACKUP_DIR/$TIMESTAMP/" 2>/dev/null

# Keep a "latest" copy
rsync -a --delete "$HOME/.aws/" "$BACKUP_DIR/latest/" 2>/dev/null

# Remove backups older than 30 days
find "$BACKUP_DIR" -maxdepth 1 -type d -name "20*" -mtime +30 -exec rm -rf {} + 2>/dev/null
