#!/usr/bin/env bash
# Start a VR-HE development session with the user's requested MAX effort.
set -euo pipefail

vrhe_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$vrhe_repo_root"

if ! command -v claude >/dev/null 2>&1; then
  printf '%s\n' 'Claude Code is not on PATH. Install or locate it, then retry this launcher.' >&2
  exit 127
fi

# Scope the request to this process and its children. No global settings are edited.
export CLAUDE_CODE_EFFORT_LEVEL=max
printf '%s\n' 'VR-HE: requesting MAX effort. Verify MAX in Claude before build work.'
exec claude --effort max "$@"
