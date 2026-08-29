# Frozen Agent Skills Authoring Contract

> **Status: FROZEN.** This file and everything under `evals/` are the bakeoff contract. Authors must not edit them. Any change after version pinning invalidates the run.

## Objective

Author the same three open-format Agent Skills without seeing or modifying the hidden evaluation fixtures. The skills must form a measured optimization pipeline:

**understand project → profile real hotspots → apply one isomorphic rewrite → verify → repeat N times**

Do not optimize an application while authoring these skills. Create reusable skill packages only.

## Allowed author output

Each author may write only:

- `./skills/`
- `./VALUE.md`
- `./SKILL_MAP.md`

Do not write anywhere else. Do not inspect the other author's directory. Do not touch `../../evals/`.

## Skills to author

1. `profiling-software-performance`
2. `extreme-software-optimization`
3. `repeatedly-apply-skill`

Use the open Agent Skills layout:

```text
<name>/
  SKILL.md
  scripts/       # optional executable helpers
  references/    # optional, one level deep from SKILL.md
  assets/        # optional templates and static inputs
```

## Design rules

- The frontmatter `name` must match the folder name, use kebab-case, and be no longer than 64 characters.
- The frontmatter `description` must be no longer than 1,024 characters, use third person, and state **WHAT the skill does, WHEN it should trigger, and when it should NOT trigger**.
- Each `SKILL.md` body must contain fewer than 500 lines.
- Reference files must be one directory level below `SKILL.md`; do not create nested reference trees.
- Scripts are executed for their outputs. Do not dump script source into model context as a substitute for running it.
- Do not merge profiling and rewriting into one skill.
- `profiling-software-performance` identifies and measures the real hotspot, then hands off a hotspot card. It does not perform the rewrite.
- `extreme-software-optimization` consumes a hotspot card and applies exactly one optimization lever per pass. It does not independently redo broad profiling.
- `repeatedly-apply-skill` is a meta-controller. It records every pass in a ledger and decides whether to KEEP, REVERT, or STOP.
- Rewrites must be isomorphic: externally observable outputs and required behavior stay unchanged.
- Do not copy, paraphrase closely, or reconstruct any paid `jeffreys-skills.md` text. Produce original work from this contract.

## Required contents

### 1. `profiling-software-performance`

Required files:

```text
skills/profiling-software-performance/
  SKILL.md
  scripts/detect_stack.sh
  scripts/run_baseline.py
  scripts/parse_profile.py
  scripts/compare_runs.py
  assets/handoff-card.md
```

The skill must produce a hotspot card containing, at minimum: project context, workload, baseline command, baseline measurements, hotspot location, hotspot class, evidence, behavioral constraints, and the recommended next measurement. The card is a handoff, not an optimization plan containing multiple rewrites.

### 2. `extreme-software-optimization`

Required files:

```text
skills/extreme-software-optimization/
  SKILL.md
  scripts/golden_check.sh
  scripts/bench_delta.py
  references/isomorphism.md
  references/branchless-classify.md
  references/lookup-tables.md
  references/arena-not-heap.md
  references/precomputed-trie.md
  references/prefix-sums.md
  references/buffer-presize.md
  references/zero-copy.md
  references/stack-scratch.md
  references/unroll-hot-loop.md
  references/allocation-elimination.md
  references/fast-path-guards.md
  references/simd-or-chunk.md
```

The twelve required pattern files are:

1. `branchless-classify`
2. `lookup-tables`
3. `arena-not-heap`
4. `precomputed-trie`
5. `prefix-sums`
6. `buffer-presize`
7. `zero-copy`
8. `stack-scratch`
9. `unroll-hot-loop`
10. `allocation-elimination`
11. `fast-path-guards`
12. `simd-or-chunk`

The skill must consume a hotspot card, select one lever, make one behavior-preserving rewrite, run correctness checks, measure the same workload, and return a KEEP or REVERT decision with evidence.

### 3. `repeatedly-apply-skill`

Required files:

```text
skills/repeatedly-apply-skill/
  SKILL.md
  scripts/next_pass.py
  assets/pass-ledger.md
```

The controller must maintain a pass ledger with: pass number, input hotspot card, chosen skill, single lever, files changed, correctness result, before/after measurements, decision, revert evidence when applicable, remaining hotspot, and stop rationale. It must not silently retain a failed or regressing rewrite.

## Author deliverables

A submission is complete only when all of the following are true:

- All three skill folders are valid and use the required layout.
- Every required script executes successfully for a representative invocation and has clear usage behavior.
- `VALUE.md` lists the files created and reports concrete validation numbers, including script/test counts and any measured execution results.
- `SKILL_MAP.md` explains activation boundaries, handoffs, and the three-skill pipeline.
- No output exists outside `./skills`, `./VALUE.md`, and `./SKILL_MAP.md`.
- No application or evaluation fixture has been optimized during authoring.

Stop once those conditions are met.
