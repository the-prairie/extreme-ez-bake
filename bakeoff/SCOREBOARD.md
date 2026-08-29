# Extreme EZ Bake Scoreboard

## Pinned environment

<!-- versions:start -->
- Date: `2026-08-29T07:08:58Z`
- Codex: `not installed`
- Claude Code: `not installed`
- Git commit: `478e9aecc7b42a4ab65701f5f6d4c96653ab0e60`
- Python: `Python 3.13.5`
- Frozen SPEC SHA-256: `6960bb511b69562acd4476288fe5c0438f6cee987e07180aff5be016d10f34c3`
- Frozen evals SHA-256: `664c8f3f2614c82ec6584c0b4ce3db5ae1c5129b7633c9b15f105ff593aa2682`
<!-- versions:end -->

## Results

<!-- results:start -->
| pack | solver | fixture | gates passed | KEEP wins | p50 speedup | false-opt | tokens | cost | lift | notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
|  |  |  |  |  |  |  |  |  |  |  |
<!-- results:end -->

## Winner rule

1. Highest mean skill lift across solvers.
2. If tied, lower false-optimize rate.
3. If still tied, better lift when the pack is used by the other model.
4. Cost is reported but is not a deciding factor unless lift is within 5%.

`skill_lift` is intentionally null in an individual grader result until a comparable no-pack control exists for the same solver, fixture, and run index.
