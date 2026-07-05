#!/usr/bin/env bash
# Read-only GitHub wrapper — reference template for the pattern documented
# in Scripts/harness/secure/README.md. Relies entirely on `gh`'s own already
# established authentication; never touches a token directly. Mutating
# operations (push, merge, label, settings changes, releases) are
# intentionally not supported here — use gh directly, with normal
# permission prompts, for those.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  github_readonly.sh repo-list <owner> [limit]
  github_readonly.sh repo-view <owner/repo>
  github_readonly.sh pr-list <owner/repo> [limit]
  github_readonly.sh issue-list <owner/repo> [limit]

All commands are read-only and scoped. Do not pass secrets on the command line.
USAGE
}

cmd="${1:-}"
shift || true

case "$cmd" in
  repo-list)
    owner="${1:?owner is required}"
    limit="${2:-50}"
    gh repo list "$owner" --limit "$limit" --json nameWithOwner,isPrivate,updatedAt,url
    ;;
  repo-view)
    repo="${1:?owner/repo is required}"
    gh repo view "$repo" --json nameWithOwner,isPrivate,defaultBranchRef,updatedAt,url
    ;;
  pr-list)
    repo="${1:?owner/repo is required}"
    limit="${2:-20}"
    gh pr list --repo "$repo" --limit "$limit" --json number,title,state,author,url
    ;;
  issue-list)
    repo="${1:?owner/repo is required}"
    limit="${2:-20}"
    gh issue list --repo "$repo" --limit "$limit" --json number,title,state,author,url
    ;;
  ""|-h|--help)
    usage
    ;;
  *)
    echo "unsupported or unsafe operation: $cmd" >&2
    usage >&2
    exit 2
    ;;
esac
