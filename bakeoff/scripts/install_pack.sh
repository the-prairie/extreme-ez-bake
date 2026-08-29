#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 PACK_DIR TARGET_WORKSPACE" >&2
  exit 2
fi
PACK_DIR="$1"
TARGET="$2"

if [[ ! -d "$TARGET" ]]; then
  echo "target workspace does not exist: $TARGET" >&2
  exit 2
fi
if [[ ! -d "$PACK_DIR" ]]; then
  echo "pack directory not found; installed 0 skills: $PACK_DIR" >&2
  exit 0
fi
SOURCE="$PACK_DIR"
if [[ -d "$PACK_DIR/skills" ]]; then
  SOURCE="$PACK_DIR/skills"
fi

AGENTS_TARGET="$TARGET/.agents/skills"
CLAUDE_TARGET="$TARGET/.claude/skills"
mkdir -p "$AGENTS_TARGET" "$CLAUDE_TARGET"

count=0
for skill_dir in "$SOURCE"/*; do
  [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
  name="$(basename "$skill_dir")"
  rm -rf "$AGENTS_TARGET/$name" "$CLAUDE_TARGET/$name"
  cp -R "$skill_dir" "$AGENTS_TARGET/$name"
  cp -R "$skill_dir" "$CLAUDE_TARGET/$name"
  count=$((count + 1))
done
printf 'Installed %d skill(s) from %s into %s and %s\n' "$count" "$PACK_DIR" "$AGENTS_TARGET" "$CLAUDE_TARGET" >&2
