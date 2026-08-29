# `bakeoff-t0` preflight

Complete this checklist in order before launching either author:

- [ ] Fixture tests pass.
- [ ] `python bakeoff/evals/grader/grade.py --help` works.
- [ ] `bakeoff/scripts/pin_versions.sh` has written the real environment details into `bakeoff/SCOREBOARD.md`.
- [ ] Commit the frozen preflight state.
- [ ] Tag that commit as `bakeoff-t0`.
- [ ] Push the commit and tag with `git push` and `git push --tags`.
- [ ] Only then run `author-codex` or `author-fable`.

After the tag exists, do not change `bakeoff/SPEC.md` or `bakeoff/evals/` for this bakeoff.
