# Extreme EZ Bake Scoreboard

## Pinned environment

<!-- versions:start -->
_Not pinned yet. Run `./scripts/pin_versions.sh` before authoring._
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
