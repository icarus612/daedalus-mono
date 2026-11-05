# pr-review

## Round 1 — 11-05-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 2
```

### Findings
- [non-blocking] libs/python/anki-tools/anki_tools/due_plan.py `_check_post_conditions`: `max_per_day` param is unused after the max loop moved to `_enforce_hard_bounds` (already noted by code-review round 1; still present).
- [non-blocking] due_plan.py `apply_shape_pass`/`apply_min_pass(keep=)`: sliding-mode hard-floor change is outside the original plan text; justified (prevents spurious `min unmet`) and tested, but should be recorded as a plan amendment.

Verified: verify-run-scope.sh OK (12 files claimed); exempt tail removed; `min unmet`/`max unmet` raise before any write; `--range` LO 0 and `--start-offset` default 0 in both CLIs; full suite 2808 passed, 18 skipped; docs README and changelog updated. 2 ruff errors are in files outside this diff (pre-existing per code-review). Severity profile: none applied.

### Open questions
- None.
