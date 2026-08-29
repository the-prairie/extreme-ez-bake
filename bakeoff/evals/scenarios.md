# Frozen evaluation scenarios

The solver matrix evaluates three small Python projects. Tests and golden output define correctness; fixture benchmarks define the targeted performance measure.

| Fixture | Planted bottleneck | Expected hotspot class | Target workload |
|---|---|---|---|
| `hyphen-naive` | Per-word linear scan of a pattern list | algo / lookup-table / trie | 5,000 words |
| `parse-branchy` | Long `if`/`elif` byte classifier | branch / lookup-table | 2 MiB input |
| `alloc-churn` | Per-item list/dict allocations in a hot loop | alloc / arena | 50,000 records |

A valid solver run measures before editing, preserves tests and golden output, changes one optimization lever per pass, and records before/after benchmark JSON. The grader considers a targeted p50 improvement of at least 20% a win. A second pass must either produce another measured KEEP or record a justified stop. Failed or regressing rewrites must be reverted.

The complete matrix is:

- solver: `codex`, `claude`
- pack: `none`, `codex`, `fable`
- fixture: `hyphen-naive`, `parse-branchy`, `alloc-churn`
- repetitions: one by default, configurable with `--runs N`
