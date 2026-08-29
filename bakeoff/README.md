# Extreme EZ Bake: sealed Agent Skills bakeoff

This harness gives Codex and Claude Code the same frozen authoring contract, packages their independent outputs, runs each pack against the same deterministic fixtures, and scores results with one grader. The author directories are separate. `evals/` is frozen. Packs are copied outputs and are never used as shared author workspaces.

## Run the bakeoff

From `bakeoff/`:

```bash
./scripts/pin_versions.sh
```

This records the date, available CLI versions, repository commit, and Python version in `SCOREBOARD.md`. Pin before either author runs.

Emit an author command without executing it:

```bash
./scripts/run_bakeoff.sh --phase author-codex
./scripts/run_bakeoff.sh --phase author-fable
```

Add `--execute` only when the corresponding CLI is installed and you intentionally want to start that author. The author writes only in its own directory. After a successful author run, the runner snapshots `skills/`, `VALUE.md`, and `SKILL_MAP.md` into the matching output-only pack.

Lint both packs:

```bash
./scripts/run_bakeoff.sh --phase lint
```

Run the full solver matrix three times per cell:

```bash
./scripts/run_bakeoff.sh --phase solve --runs 3
```

The matrix crosses two solvers (`codex`, `claude`), three packs (`none`, `codex`, `fable`), and three fixtures. Missing CLIs do not abort setup: the runner prints the command it would have used and continues. Completed run traces and grader JSON land in `runs/solving/`.

Aggregate completed results:

```bash
./scripts/run_bakeoff.sh --phase score
```

Read `SCOREBOARD.md` for pinned versions, cell results, the winner rule, and notes. Do not edit `evals/` after pinning; an authoring execution checks the frozen tree before and after the run.
