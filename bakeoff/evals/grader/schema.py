"""Frozen trace contract for the Extreme EZ Bake grader.

A solver trace is optional. When supplied, it must be a JSON object shaped like:

{
  "schema_version": 1,
  "run_id": "codex-codex-hyphen-naive-1",
  "solver": "codex",
  "pack": "codex",
  "fixture": "hyphen-naive",
  "hotspot_class": "lookup-table",
  "benchmarks": {
    "before": {"scenario": "hyphen-naive", "p50_ms": 20.0, "p95_ms": 22.0},
    "after": {"scenario": "hyphen-naive", "p50_ms": 8.0, "p95_ms": 9.0}
  },
  "events": [
    {"seq": 1, "type": "benchmark_before", "command": "python bench.py"},
    {"seq": 2, "type": "hotspot_card", "class": "lookup-table"},
    {"seq": 3, "type": "edit", "files": ["main.py"]},
    {
      "seq": 4,
      "type": "optimization_pass",
      "pass": 1,
      "lever": "lookup-table",
      "decision": "KEEP",
      "before_p50_ms": 20.0,
      "after_p50_ms": 8.0,
      "justification": "Tests and golden output pass; p50 improved."
    },
    {"seq": 5, "type": "tests", "passed": true},
    {"seq": 6, "type": "benchmark_after", "command": "python bench.py"}
  ],
  "usage": {"tokens": null, "cost": null}
}

Benchmark values may instead be paths to JSON files, relative to the trace file.
Events are ordered by list position; `seq` is recommended evidence, not required.
Unknown event fields are allowed. The grader never executes commands from a trace.

Gate event expectations:
- G1: a baseline/benchmark-before event precedes the first edit event.
- G3: each optimization-pass event declares exactly one `lever` (or one-item `levers`).
- G7: pass 2 is KEEP, or a STOP event/pass has a non-empty justification.
- G10: every `bad_rewrite` event is followed by a matching `revert`, or the pass decision is REVERT.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

GateStatus = Literal["pass", "fail", "skip"]


class Benchmark(TypedDict, total=False):
    scenario: str
    p50_ms: float
    p95_ms: float
    note: str


class ToolEvent(TypedDict, total=False):
    seq: int
    type: str
    command: str
    files: list[str]
    class_: str
    pass_: int
    lever: str
    levers: list[str]
    decision: str
    justification: str
    passed: bool


class Trace(TypedDict, total=False):
    schema_version: int
    run_id: str
    solver: str
    pack: str
    fixture: str
    hotspot_class: str
    hotspot_card: dict[str, Any]
    benchmarks: dict[str, Benchmark | str]
    events: list[dict[str, Any]]
    usage: dict[str, Any]


EXPECTED_HOTSPOT_CLASSES: dict[str, set[str]] = {
    "hyphen-naive": {"algo", "lookup-table", "trie"},
    "parse-branchy": {"branch", "lookup-table"},
    "alloc-churn": {"alloc", "arena"},
}

REQUIRED_SKILLS = (
    "profiling-software-performance",
    "extreme-software-optimization",
    "repeatedly-apply-skill",
)

REQUIRED_FILES: dict[str, tuple[str, ...]] = {
    "profiling-software-performance": (
        "SKILL.md",
        "scripts/detect_stack.sh",
        "scripts/run_baseline.py",
        "scripts/parse_profile.py",
        "scripts/compare_runs.py",
        "assets/handoff-card.md",
    ),
    "extreme-software-optimization": (
        "SKILL.md",
        "scripts/golden_check.sh",
        "scripts/bench_delta.py",
        "references/isomorphism.md",
        "references/branchless-classify.md",
        "references/lookup-tables.md",
        "references/arena-not-heap.md",
        "references/precomputed-trie.md",
        "references/prefix-sums.md",
        "references/buffer-presize.md",
        "references/zero-copy.md",
        "references/stack-scratch.md",
        "references/unroll-hot-loop.md",
        "references/allocation-elimination.md",
        "references/fast-path-guards.md",
        "references/simd-or-chunk.md",
    ),
    "repeatedly-apply-skill": (
        "SKILL.md",
        "scripts/next_pass.py",
        "assets/pass-ledger.md",
    ),
}
