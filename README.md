# extreme-ez-bake
A bake-off between GPT 5.6 SOL and Fable 5 to create software optimization skills

## What this compares

Codex and Claude Code independently author the same three open-format Agent Skills from one frozen contract:

- `profiling-software-performance`
- `extreme-software-optimization`
- `repeatedly-apply-skill`

Their skill packs are then installed into isolated workspaces and tested across the same three deterministic performance fixtures. Both Codex and Claude solve every fixture with no pack, the Codex-authored pack, and the Fable-authored pack. A frozen grader scores correctness, measured speedup, process gates, activation behavior, and skill lift.

## Repository layout

```text
bakeoff/
  SPEC.md          frozen authoring contract
  evals/           frozen fixtures, prompts, and grader
  authors/         isolated Codex and Fable author workspaces
  packs/           committed snapshots of completed author outputs
  runs/            generated authoring and solving traces (gitignored)
  scripts/         pin, isolate, install, run, and score helpers
  SCOREBOARD.md    pinned environment and bakeoff results
```

See [`bakeoff/README.md`](bakeoff/README.md) for the operational guide and matrix details.

## Prerequisites

- Python 3
- `pytest` is optional; the committed tests also run with Python's built-in `unittest`
- Codex CLI for Codex authoring and solver cells
- Claude Code CLI for Fable authoring and Claude solver cells

Missing agent CLIs do not prevent linting or fixture validation. The runner prints commands for missing tools rather than failing the whole setup.

## Freeze before authoring

> **Pin and tag the repository before either author runs.** Do not launch `author-codex` or `author-fable` until the `bakeoff-t0` tag has been created and pushed.

After `bakeoff-t0`, do not edit `bakeoff/SPEC.md` or anything under `bakeoff/evals/`. Those files define the sealed contract and grader. Any later change invalidates comparability with the tagged baseline.

Use the root [`PREFLIGHT.md`](PREFLIGHT.md) checklist before creating the tag.

## Commands

From the repository root:

```bash
cd bakeoff

# Record the date, available CLI versions, Git commit, Python version,
# and frozen SPEC/evals hashes in SCOREBOARD.md.
./scripts/pin_versions.sh

# Commit the resulting preflight state, create bakeoff-t0, and push the tag
# before continuing beyond this point.

# Emit author commands without running them.
./scripts/run_bakeoff.sh --phase author-codex
./scripts/run_bakeoff.sh --phase author-fable

# Add --execute only after bakeoff-t0 exists and has been pushed.
./scripts/run_bakeoff.sh --phase author-codex --execute
./scripts/run_bakeoff.sh --phase author-fable --execute

# Lint completed output packs.
./scripts/run_bakeoff.sh --phase lint

# Run every solver/pack/fixture cell three times.
./scripts/run_bakeoff.sh --phase solve --runs 3

# Aggregate completed grader outputs into SCOREBOARD.md.
./scripts/run_bakeoff.sh --phase score
```
