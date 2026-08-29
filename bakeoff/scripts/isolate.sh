#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 NAME" >&2
  echo "NAME is a fixture folder under evals/fixtures; set PACK_DIR to install a pack." >&2
  exit 2
fi
NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAKEOFF_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURE_DIR="${FIXTURE_DIR:-$BAKEOFF_ROOT/evals/fixtures/$NAME}"
PACK="${PACK_DIR:-}"
SAFE_NAME="$(printf '%s' "$NAME" | tr -cd 'A-Za-z0-9._-')"
WORKSPACE="$(mktemp -d "${TMPDIR:-/tmp}/extreme-ez-bake-${SAFE_NAME}.XXXXXX")"

if [[ ! -d "$FIXTURE_DIR" ]]; then
  rm -rf "$WORKSPACE"
  echo "fixture not found: $FIXTURE_DIR" >&2
  exit 2
fi
cp -R "$FIXTURE_DIR"/. "$WORKSPACE"/
chmod -R u+w "$WORKSPACE"

# Solvers may edit implementation files, but fixture contracts remain read-only.
find "$WORKSPACE" -maxdepth 1 -type f \( -name 'test_*.py' -o -name 'bench.py' -o -name 'golden.txt' -o -name 'README.md' \) -exec chmod a-w {} +

if [[ -n "$PACK" && "$PACK" != "none" ]]; then
  "$SCRIPT_DIR/install_pack.sh" "$PACK" "$WORKSPACE"
fi
printf '%s\n' "$WORKSPACE"
