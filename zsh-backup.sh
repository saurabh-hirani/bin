#!/bin/bash

BACKUP_DIR="$HOME/backups/zsh-backups"
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")

# Create timestamped backups
cp "$HOME/.zshrc" "$BACKUP_DIR/.zshrc/.zshrc.$TIMESTAMP" 2>/dev/null
cp "$HOME/.zsh_history" "$BACKUP_DIR/.zsh_history/.zsh_history.$TIMESTAMP" 2>/dev/null

# Backup current files
cp "$HOME/.zshrc" "$BACKUP_DIR/.zshrc/" 2>/dev/null
cp "$HOME/.zsh_history" "$BACKUP_DIR/.zsh_history/" 2>/dev/null

# Create full history - properly combine preserving multiline commands
# from https://david-kerwick.github.io/2017-01-04-combining-zsh-history-files/
MARKER="MULTILINE_$(date +"%s")"
if [[ -f "$BACKUP_DIR/.zsh_history.full" ]]; then
  FULL_FILE="$BACKUP_DIR/.zsh_history.full"
else
  FULL_FILE=""
fi
LC_ALL=C cat $FULL_FILE "$BACKUP_DIR"/.zsh_history/.zsh_history.* 2>/dev/null | \
  LC_ALL=C awk -v marker="$MARKER" '{if (sub(/\\$/,marker)) printf "%s", $0; else print $0}' | \
  LC_ALL=C sort -u | \
  LC_ALL=C awk -v marker="$MARKER" '{gsub(marker,"\\\n"); print $0}' > "$BACKUP_DIR/.zsh_history.full.tmp" && \
  mv "$BACKUP_DIR/.zsh_history.full.tmp" "$BACKUP_DIR/.zsh_history.full"

# Remove old files
find "$BACKUP_DIR/.zshrc" -name ".zshrc.*" -mtime +30 -delete 2>/dev/null
find "$BACKUP_DIR/.zsh_history" -name ".zsh_history.*" -mtime +60 -delete 2>/dev/null
