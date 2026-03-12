#!/bin/bash
set -e

if [ $# -lt 3 ] || [ $# -gt 4 ]; then
  echo "Usage: $0 <public-repo-url> <base-dir> <new-origin-user> [REPO_CREATE=0|1]"
  exit 1
fi

PUBLIC_REPO="$1"
BASE_DIR="$2"
NEW_USER="$3"
REPO_CREATE="${4:-0}"
REPO_NAME=$(basename "$PUBLIC_REPO" .git)
NEW_ORIGIN="git@github.com:$NEW_USER/$REPO_NAME.git"

git clone --bare "$PUBLIC_REPO" temp-bare
mkdir -p "$BASE_DIR"
git clone "temp-bare" "$BASE_DIR/$REPO_NAME"
cd "$BASE_DIR/$REPO_NAME"
git remote set-url origin "$NEW_ORIGIN"
git remote add public "$PUBLIC_REPO"

# Ensure we're on main branch (rename if needed)
git checkout -b main 2>/dev/null || git checkout main

if [ "$REPO_CREATE" = "1" ]; then
  gh repo create "$NEW_USER/$REPO_NAME" --private
  git push -u origin main
fi

cd - > /dev/null
rm -rf temp-bare

echo "Private fork created in $BASE_DIR/$REPO_NAME"
echo "Origin set to $NEW_ORIGIN"
