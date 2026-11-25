#!/bin/bash
# Clone a GitHub repo over HTTPS (or fix an existing clone) when SSH port 22 is blocked.

set -eou pipefail

usage() {
  cat >&2 <<EOF
Usage: $(basename "$0") <repo-url> <parent-dir> [options]

Clone a GitHub repo into <parent-dir>/<repo-name> over HTTPS and set per-repo config
so push works without SSH. If the repo is already cloned there, fix its remote and
config instead.

Why: ~/.gitconfig rewrites https://github.com/ to SSH. Putting the username in the
URL skips the rewrite. 'gh' supplies the credentials.

Arguments:
  repo-url        GitHub repo URL (https, git@github.com:, or ssh://) or owner/repo
  parent-dir      Directory that holds (or will hold) the clone

Options:
  --user NAME     GitHub username put in the remote URL (default: saurabh-hirani)
  --name NAME     git user.name to set (default: Saurabh Hirani)
  --email EMAIL   git user.email to set (default: saurabh.hirani@gmail.com)
  -h, --help      Show this help message

Behaviour:
  Not cloned yet:  gh repo view, git clone with username URL, set credential.helper,
                   user.name, user.email, then git ls-remote.
  Already cloned:  set origin to the username URL, set credential.helper, set
                   user.name/user.email only if the repo has none, then git ls-remote.
  Path exists but is not a git repo (or is a clone of another repo): exit 1.

Output:
  Prints the absolute repo path to stdout.

Examples:
  $(basename "$0") https://github.com/OWNER/REPO.git ~/github/OWNER
  $(basename "$0") saurabh-hirani/bin ~/github/saurabh-hirani
EOF
}

check_prereqs() {
  local missing=()
  for cmd in git gh sed; do
    if ! command -v "$cmd" &>/dev/null; then
      missing+=("$cmd")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "Missing required commands: ${missing[*]}" >&2
    exit 1
  fi
}

log() {
  echo "$*" >&2
}

die() {
  echo "error=$*" >&2
  exit 1
}

# Print "owner/repo" for a GitHub URL or owner/repo shorthand.
parse_slug() {
  local url="$1" slug
  case "$url" in
    *github.com[:/]*)
      slug=$(sed -E 's#^.*github\.com[:/]+##; s#\.git/?$##; s#/+$##' <<<"$url")
      ;;
    */*)
      if [[ "$url" == *:* ]]; then
        die "unsupported url (only github.com): $url"
      fi
      slug=$(sed -E 's#\.git/?$##; s#/+$##' <<<"$url")
      ;;
    *)
      die "cannot parse repo url: $url"
      ;;
  esac
  if [[ ! "$slug" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
    die "cannot parse owner/repo from: $url"
  fi
  echo "$slug"
}

set_config() {
  local dir="$1" name="$2" email="$3" only_if_unset="$4"
  git -C "$dir" config credential.helper '!gh auth git-credential'
  if [[ "$only_if_unset" == "yes" ]]; then
    git -C "$dir" config --local --get user.name &>/dev/null || git -C "$dir" config user.name "$name"
    git -C "$dir" config --local --get user.email &>/dev/null || git -C "$dir" config user.email "$email"
  else
    git -C "$dir" config user.name "$name"
    git -C "$dir" config user.email "$email"
  fi
}

verify() {
  local dir="$1"
  log "action=verify path=$dir"
  git -C "$dir" remote -v >&2
  git -C "$dir" ls-remote --heads origin >&2
}

clone_new() {
  local slug="$1" remote="$2" dir="$3" name="$4" email="$5"
  log "action=gh_repo_view repo=$slug"
  gh repo view "$slug" --json nameWithOwner -q .nameWithOwner >&2 ||
    die "repo not found or no access: $slug (try: gh auth status, gh auth refresh -s repo)"
  log "action=clone remote=$remote path=$dir"
  git clone "$remote" "$dir" >&2
  set_config "$dir" "$name" "$email" no
}

fix_existing() {
  local slug="$1" remote="$2" dir="$3" name="$4" email="$5" current
  current=$(git -C "$dir" remote get-url origin 2>/dev/null) ||
    die "existing repo has no origin remote: $dir"
  if [[ "$(parse_slug "$current")" != "$slug" ]]; then
    die "existing repo at $dir has origin $current, expected $slug"
  fi
  log "action=set_remote path=$dir remote=$remote"
  git -C "$dir" remote set-url origin "$remote"
  set_config "$dir" "$name" "$email" yes
}

main() {
  local url="" parent="" user="saurabh-hirani" name="Saurabh Hirani" email="saurabh.hirani@gmail.com"
  local args=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h | --help)
        usage
        exit 0
        ;;
      --user)
        user="${2:?--user needs a value}"
        shift 2
        ;;
      --name)
        name="${2:?--name needs a value}"
        shift 2
        ;;
      --email)
        email="${2:?--email needs a value}"
        shift 2
        ;;
      -*)
        usage
        die "unknown option: $1"
        ;;
      *)
        args+=("$1")
        shift
        ;;
    esac
  done

  if [[ ${#args[@]} -ne 2 ]]; then
    usage
    die "expected <repo-url> <parent-dir>"
  fi
  url="${args[0]}"
  parent="${args[1]}"

  check_prereqs

  local slug repo remote dir
  slug=$(parse_slug "$url")
  repo="${slug#*/}"
  remote="https://${user}@github.com/${slug}.git"

  [[ -d "$parent" ]] || die "parent dir does not exist: $parent"
  parent=$(cd "$parent" && pwd)
  dir="$parent/$repo"

  if [[ -d "$dir/.git" ]]; then
    log "state=already_cloned path=$dir"
    fix_existing "$slug" "$remote" "$dir" "$name" "$email"
  elif [[ -e "$dir" ]] && [[ -n "$(ls -A "$dir" 2>/dev/null)" || ! -d "$dir" ]]; then
    die "path exists and is not a git repo: $dir"
  else
    log "state=not_cloned path=$dir"
    clone_new "$slug" "$remote" "$dir" "$name" "$email"
  fi

  verify "$dir"
  echo "$dir"
}

main "$@"
