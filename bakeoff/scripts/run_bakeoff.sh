#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAKEOFF_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BAKEOFF_ROOT/.." && pwd)"
GRADER="$BAKEOFF_ROOT/evals/grader/grade.py"
SOLVER_PROMPT="$BAKEOFF_ROOT/evals/prompts/solver.txt"
SCOREBOARD="$BAKEOFF_ROOT/SCOREBOARD.md"
PHASE=""
RUNS=1
EXECUTE=0

usage() {
  cat <<'EOF'
usage: ./scripts/run_bakeoff.sh --phase PHASE [--runs N] [--execute]

phases:
  pin            pin tool/repo versions and freeze evals
  author-codex   emit the Codex author command; run it only with --execute
  author-fable   emit the Fable author command; run it only with --execute
  lint           statically lint both output packs
  solve          run/emit the 2 x 3 x 3 solver matrix
  score          aggregate completed *.grade.json results into SCOREBOARD.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --phase) PHASE="${2:-}"; shift 2 ;;
    --runs) RUNS="${2:-}"; shift 2 ;;
    --execute) EXECUTE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
if [[ -z "$PHASE" ]]; then
  echo "--phase is required" >&2
  usage >&2
  exit 2
fi
if ! [[ "$RUNS" =~ ^[1-9][0-9]*$ ]]; then
  echo "--runs must be a positive integer" >&2
  exit 2
fi

SPEC_DIGEST() {
  python - "$BAKEOFF_ROOT/SPEC.md" <<'PY'
import hashlib
import sys
from pathlib import Path
print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
PY
}

EVALS_DIGEST() {
  python - "$BAKEOFF_ROOT/evals" <<'PY'
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
}

AUTHOR_GUARD_DIGEST() {
  local author="$1"
  python - "$REPO_ROOT" "$author" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
author = sys.argv[2]
allowed_prefix = Path("bakeoff/authors") / author / "skills"
allowed_exact = {
    Path("bakeoff/authors") / author / "VALUE.md",
    Path("bakeoff/authors") / author / "SKILL_MAP.md",
}
digest = hashlib.sha256()
for path in sorted(root.rglob("*")):
    rel = path.relative_to(root)
    if not rel.parts or rel.parts[0] == ".git":
        continue
    if rel == allowed_prefix or allowed_prefix in rel.parents or rel in allowed_exact:
        continue
    if "__pycache__" in rel.parts or path.suffix == ".pyc":
        continue
    kind = "L" if path.is_symlink() else "D" if path.is_dir() else "F"
    digest.update(kind.encode())
    digest.update(b"\0")
    digest.update(rel.as_posix().encode())
    digest.update(b"\0")
    digest.update(oct(path.lstat().st_mode & 0o777).encode())
    digest.update(b"\0")
    if path.is_symlink():
        digest.update(os.readlink(path).encode())
    elif path.is_file():
        digest.update(path.read_bytes())
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

pinned_spec_digest() {
  python - "$SCOREBOARD" <<'PY'
import re
import sys
from pathlib import Path
match = re.search(r"Frozen SPEC SHA-256: `([0-9a-f]{64})`", Path(sys.argv[1]).read_text(encoding="utf-8"))
print(match.group(1) if match else "")
PY
}

pinned_digest() {
  python - "$SCOREBOARD" <<'PY'
import re
import sys
from pathlib import Path
match = re.search(r"Frozen evals SHA-256: `([0-9a-f]{64})`", Path(sys.argv[1]).read_text(encoding="utf-8"))
print(match.group(1) if match else "")
PY
}

require_pin() {
  local pinned current pinned_spec current_spec
  pinned="$(pinned_digest)"
  pinned_spec="$(pinned_spec_digest)"
  if [[ -z "$pinned" || -z "$pinned_spec" ]]; then
    echo "authoring requires a pinned environment; run ./scripts/pin_versions.sh first" >&2
    return 2
  fi
  current="$(EVALS_DIGEST)"
  current_spec="$(SPEC_DIGEST)"
  if [[ "$pinned" != "$current" ]]; then
    echo "frozen evals digest changed: pinned=$pinned current=$current" >&2
    return 2
  fi
  if [[ "$pinned_spec" != "$current_spec" ]]; then
    echo "frozen SPEC digest changed: pinned=$pinned_spec current=$current_spec" >&2
    return 2
  fi
}

publish_pack() {
  local author="$1" pack="$2"
  local source="$BAKEOFF_ROOT/authors/$author"
  local target="$BAKEOFF_ROOT/packs/$pack"
  mkdir -p "$target"
  find "$target" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -exec rm -rf {} +
  if [[ -d "$source/skills" ]]; then
    for skill in "$source/skills"/*; do
      [[ -d "$skill" ]] || continue
      cp -R "$skill" "$target/$(basename "$skill")"
    done
  fi
  [[ -f "$source/VALUE.md" ]] && cp "$source/VALUE.md" "$target/VALUE.md"
  [[ -f "$source/SKILL_MAP.md" ]] && cp "$source/SKILL_MAP.md" "$target/SKILL_MAP.md"
  printf 'Published immutable snapshot from authors/%s to packs/%s\n' "$author" "$pack"
}

run_author() {
  local author="$1" tool="$2" command_text="$3"
  echo "$command_text"
  [[ "$EXECUTE" -eq 1 ]] || return 0
  require_pin
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "$tool is not installed; command emitted but not executed" >&2
    return 0
  fi
  local before after before_spec after_spec before_guard after_guard status log final_log stamp
  before="$(EVALS_DIGEST)"
  before_spec="$(SPEC_DIGEST)"
  before_guard="$(AUTHOR_GUARD_DIGEST "$author")"
  chmod a-w "$BAKEOFF_ROOT/SPEC.md"
  find "$BAKEOFF_ROOT/evals" -type f -exec chmod a-w {} +
  find "$BAKEOFF_ROOT/evals" -type d -exec chmod a-w {} +
  stamp="$(date -u +'%Y%m%dT%H%M%SZ')"
  final_log="$BAKEOFF_ROOT/runs/authoring/${author}-${stamp}.log"
  log="$(mktemp "${TMPDIR:-/tmp}/extreme-ez-bake-${author}-author.XXXXXX.log")"
  set +e
  if [[ "$author" == "codex" ]]; then
    (cd "$BAKEOFF_ROOT/authors/codex" && codex exec --full-auto --sandbox workspace-write "$(cat ../../SPEC.md)") 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
  else
    (cd "$BAKEOFF_ROOT/authors/fable" && claude --model claude-fable-5 -p --dangerously-skip-permissions "$(cat ../../SPEC.md)") 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
  fi
  set -e
  after="$(EVALS_DIGEST)"
  after_spec="$(SPEC_DIGEST)"
  after_guard="$(AUTHOR_GUARD_DIGEST "$author")"
  mkdir -p "$(dirname "$final_log")"
  mv "$log" "$final_log"
  if [[ "$before" != "$after" || "$before_spec" != "$after_spec" ]]; then
    echo "author modified the frozen SPEC/evals contract; run invalid and pack not published" >&2
    return 3
  fi
  if [[ "$before_guard" != "$after_guard" ]]; then
    echo "author wrote outside ./skills, ./VALUE.md, or ./SKILL_MAP.md; run invalid and pack not published" >&2
    return 3
  fi
  if [[ "$status" -ne 0 ]]; then
    echo "$author author command exited with status $status; pack not published" >&2
    return "$status"
  fi
  publish_pack "$author" "$author"
}

run_lint() {
  for pack in codex fable; do
    echo "== lint: $pack =="
    python "$GRADER" --pack "$BAKEOFF_ROOT/packs/$pack" --lint-only
  done
}

emit_solver_command() {
  local solver="$1" workspace="$2"
  if [[ "$solver" == "codex" ]]; then
    printf 'cd %q && codex exec --full-auto --sandbox workspace-write "$(cat %q)"\n' "$workspace" "$SOLVER_PROMPT"
  else
    printf 'cd %q && claude --model claude-fable-5 -p --dangerously-skip-permissions "$(cat %q)"\n' "$workspace" "$SOLVER_PROMPT"
  fi
}

hash_file() {
  python - "$1" <<'PYHASH'
import hashlib
import sys
from pathlib import Path
path = Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing")
PYHASH
}

run_solver_cell() {
  local solver="$1" pack="$2" fixture="$3" index="$4"
  local tool pack_dir workspace run_id run_dir before after trace grade log main_before main_after test_status agent_status
  tool="$solver"
  [[ "$solver" == "claude" ]] && tool="claude"
  pack_dir="none"
  [[ "$pack" != "none" ]] && pack_dir="$BAKEOFF_ROOT/packs/$pack"
  run_id="${solver}-${pack}-${fixture}-${index}"
  run_dir="$BAKEOFF_ROOT/runs/solving"

  if ! command -v "$tool" >/dev/null 2>&1; then
    workspace="<isolated-${fixture}-workspace>"
    echo "[$run_id] $tool is not installed; command only:"
    emit_solver_command "$solver" "$workspace"
    return 0
  fi

  if [[ "$pack" == "none" ]]; then
    workspace="$(PACK_DIR=none "$SCRIPT_DIR/isolate.sh" "$fixture")"
  else
    workspace="$(PACK_DIR="$pack_dir" "$SCRIPT_DIR/isolate.sh" "$fixture")"
  fi
  before="$run_dir/${run_id}.before.json"
  after="$run_dir/${run_id}.after.json"
  trace="$run_dir/${run_id}.trace.json"
  grade="$run_dir/${run_id}.grade.json"
  log="$run_dir/${run_id}.solver.log"
  main_before="$(hash_file "$workspace/main.py")"

  (cd "$workspace" && python bench.py) > "$before"
  echo "[$run_id] executing:"
  emit_solver_command "$solver" "$workspace"
  set +e
  if [[ "$solver" == "codex" ]]; then
    (cd "$workspace" && codex exec --full-auto --sandbox workspace-write "$(cat "$SOLVER_PROMPT")") 2>&1 | tee "$log"
    agent_status=${PIPESTATUS[0]}
  else
    (cd "$workspace" && claude --model claude-fable-5 -p --dangerously-skip-permissions "$(cat "$SOLVER_PROMPT")") 2>&1 | tee "$log"
    agent_status=${PIPESTATUS[0]}
  fi
  (cd "$workspace" && python -m unittest discover -s . -p 'test_*.py') >/dev/null 2>&1
  test_status=$?
  (cd "$workspace" && python bench.py) > "$after"
  set -e
  main_after="$(hash_file "$workspace/main.py")"

  SOLVER="$solver" PACK="$pack" FIXTURE="$fixture" RUN_ID="$run_id" \
  BEFORE="$before" AFTER="$after" TRACE="$trace" MAIN_BEFORE="$main_before" MAIN_AFTER="$main_after" \
  AGENT_STATUS="$agent_status" TEST_STATUS="$test_status" python <<'PY'
import json
import os
from pathlib import Path

events = [{"seq": 1, "type": "benchmark_before", "command": "python bench.py"}]
if os.environ["MAIN_BEFORE"] != os.environ["MAIN_AFTER"]:
    events.append({"seq": 2, "type": "edit", "files": ["main.py"]})
events.append({"seq": len(events) + 1, "type": "tests", "passed": os.environ["TEST_STATUS"] == "0"})
events.append({"seq": len(events) + 1, "type": "benchmark_after", "command": "python bench.py"})
trace = {
    "schema_version": 1,
    "run_id": os.environ["RUN_ID"],
    "solver": os.environ["SOLVER"],
    "pack": os.environ["PACK"],
    "fixture": os.environ["FIXTURE"],
    "benchmarks": {
        "before": Path(os.environ["BEFORE"]).name,
        "after": Path(os.environ["AFTER"]).name,
    },
    "events": events,
    "agent_exit_status": int(os.environ["AGENT_STATUS"]),
    "usage": {"tokens": None, "cost": None},
}
Path(os.environ["TRACE"]).write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

  python "$GRADER" \
    --pack "$pack_dir" \
    --solver "$solver" \
    --trace "$trace" \
    --fixture "$workspace" \
    --out "$grade" >/dev/null
  echo "[$run_id] grade: $grade"
  rm -rf "$workspace"
}

run_solve() {
  mkdir -p "$BAKEOFF_ROOT/runs/solving"
  for solver in codex claude; do
    for pack in none codex fable; do
      for fixture in hyphen-naive parse-branchy alloc-churn; do
        for ((index = 1; index <= RUNS; index++)); do
          run_solver_cell "$solver" "$pack" "$fixture" "$index"
        done
      done
    done
  done
}

run_score() {
  python - "$BAKEOFF_ROOT/runs/solving" "$SCOREBOARD" <<'PY'
import json
import sys
from collections import defaultdict
from pathlib import Path

runs = Path(sys.argv[1])
scoreboard = Path(sys.argv[2])
rows = []
for path in sorted(runs.glob("*.grade.json")):
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        continue
    stem = path.name.removesuffix(".grade.json")
    trace_path = runs / f"{stem}.trace.json"
    trace = {}
    if trace_path.is_file():
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    pack = str(trace.get("pack") or Path(str(result.get("pack", ""))).name)
    solver = str(result.get("solver", ""))
    fixture = str(result.get("fixture", ""))
    gates = result.get("gates", {})
    passed = sum(1 for item in gates.values() if isinstance(item, dict) and item.get("status") == "pass")
    measured = [item.get("status") for item in gates.values() if isinstance(item, dict)]
    keep_wins = sum(1 for event in trace.get("events", []) if str(event.get("decision", "")).upper() == "KEEP")
    speedup = result.get("values", {}).get("V3")
    false_opt = ""
    if any(gates.get(name, {}).get("status") == "fail" for name in ("G4", "G5", "G6", "G10")):
        false_opt = 1
    elif speedup is not None:
        false_opt = 0
    usage = trace.get("usage", {}) if isinstance(trace.get("usage"), dict) else {}
    run_index = stem.rsplit("-", 1)[-1]
    rows.append({
        "pack": pack, "solver": solver, "fixture": fixture, "run_index": run_index,
        "gates": passed, "keep": keep_wins, "speedup": speedup, "false_opt": false_opt,
        "tokens": usage.get("tokens"), "cost": usage.get("cost"), "lift": None,
        "notes": "" if all(status != "fail" for status in measured) else "one or more gates failed",
    })

controls = {}
for row in rows:
    if row["pack"] == "none" and isinstance(row["speedup"], (int, float)):
        controls[(row["solver"], row["fixture"], row["run_index"])] = row["speedup"]
for row in rows:
    control = controls.get((row["solver"], row["fixture"], row["run_index"]))
    if row["pack"] != "none" and control and isinstance(row["speedup"], (int, float)):
        row["lift"] = row["speedup"] / control - 1.0

header = [
    "| pack | solver | fixture | gates passed | KEEP wins | p50 speedup | false-opt | tokens | cost | lift | notes |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
]
if not rows:
    table = header + ["|  |  |  |  |  |  |  |  |  |  | no completed grader results |"]
else:
    table = header
    for row in rows:
        speedup = "" if row["speedup"] is None else f"{row['speedup']:.3f}×"
        lift = "" if row["lift"] is None else f"{row['lift'] * 100:+.1f}%"
        tokens = "" if row["tokens"] is None else str(row["tokens"])
        cost = "" if row["cost"] is None else str(row["cost"])
        table.append(
            f"| {row['pack']} | {row['solver']} | {row['fixture']} | {row['gates']} | "
            f"{row['keep']} | {speedup} | {row['false_opt']} | {tokens} | {cost} | {lift} | {row['notes']} |"
        )

text = scoreboard.read_text(encoding="utf-8")
start = "<!-- results:start -->"
end = "<!-- results:end -->"
left, marker, remainder = text.partition(start)
if not marker or end not in remainder:
    raise SystemExit("SCOREBOARD.md is missing results markers")
_, _, right = remainder.partition(end)
block = start + "\n" + "\n".join(table) + "\n" + end
scoreboard.write_text(left + block + right, encoding="utf-8")
print(f"Scored {len(rows)} completed run(s) into {scoreboard}")
PY
}

case "$PHASE" in
  pin) "$SCRIPT_DIR/pin_versions.sh" ;;
  author-codex)
    run_author "codex" "codex" 'cd bakeoff/authors/codex && codex exec --full-auto --sandbox workspace-write "$(cat ../../SPEC.md)"'
    ;;
  author-fable)
    run_author "fable" "claude" 'cd bakeoff/authors/fable && claude --model claude-fable-5 -p --dangerously-skip-permissions "$(cat ../../SPEC.md)"'
    ;;
  lint) run_lint ;;
  solve) run_solve ;;
  score) run_score ;;
  *) echo "unknown phase: $PHASE" >&2; usage >&2; exit 2 ;;
esac
