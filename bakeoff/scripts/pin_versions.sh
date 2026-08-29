#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAKEOFF_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BAKEOFF_ROOT/.." && pwd)"
SCOREBOARD="$BAKEOFF_ROOT/SCOREBOARD.md"
EVALS_DIR="$BAKEOFF_ROOT/evals"

first_line() {
  "$@" 2>&1 | head -n 1 | tr -d '\r'
}

if command -v codex >/dev/null 2>&1; then
  CODEX_VERSION="$(first_line codex --version || true)"
else
  CODEX_VERSION="not installed"
fi
if command -v claude >/dev/null 2>&1; then
  CLAUDE_VERSION="$(first_line claude --version || true)"
else
  CLAUDE_VERSION="not installed"
fi
if GIT_HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null)"; then
  :
else
  GIT_HEAD="not a git checkout"
fi
PIN_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
PYTHON_VERSION="$(first_line python --version)"
SPEC_SHA="$(python - "$BAKEOFF_ROOT/SPEC.md" <<'PY'
import hashlib
import sys
from pathlib import Path
print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)"
EVALS_SHA="$(python - "$EVALS_DIR" <<'PY'
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
digest = hashlib.sha256()
for path in sorted(item for item in root.rglob("*") if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"):
    digest.update(path.relative_to(root).as_posix().encode())
    digest.update(b"\0")
    digest.update(path.read_bytes())
    digest.update(b"\0")
print(digest.hexdigest())
PY
)"

PIN_DATE="$PIN_DATE" CODEX_VERSION="$CODEX_VERSION" CLAUDE_VERSION="$CLAUDE_VERSION" \
GIT_HEAD="$GIT_HEAD" PYTHON_VERSION="$PYTHON_VERSION" SPEC_SHA="$SPEC_SHA" EVALS_SHA="$EVALS_SHA" \
python - "$SCOREBOARD" <<'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = "<!-- versions:start -->"
end = "<!-- versions:end -->"
block = "\n".join([
    start,
    f"- Date: `{os.environ['PIN_DATE']}`",
    f"- Codex: `{os.environ['CODEX_VERSION']}`",
    f"- Claude Code: `{os.environ['CLAUDE_VERSION']}`",
    f"- Git commit: `{os.environ['GIT_HEAD']}`",
    f"- Python: `{os.environ['PYTHON_VERSION']}`",
    f"- Frozen SPEC SHA-256: `{os.environ['SPEC_SHA']}`",
    f"- Frozen evals SHA-256: `{os.environ['EVALS_SHA']}`",
    end,
])
left, marker, remainder = text.partition(start)
if not marker or end not in remainder:
    raise SystemExit("SCOREBOARD.md is missing version markers")
_, _, right = remainder.partition(end)
path.write_text(left + block + right, encoding="utf-8")
PY

# Freeze the contract for authoring. Isolated solver copies are made writable later.
chmod a-w "$BAKEOFF_ROOT/SPEC.md"
find "$EVALS_DIR" -type f -exec chmod a-w {} +
find "$EVALS_DIR" -type d -exec chmod a-w {} +

printf 'Pinned environment and frozen evals in %s\n' "$SCOREBOARD"
