# code-review

## Round 1 — 11-05-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 3
```

### Findings
- [non-blocking] due_plan.py `_check_post_conditions`: `max_per_day` parameter is now unused after the max loop moved into `_enforce_hard_bounds`; drop it (exit report acknowledges it).
- [non-blocking] Unplanned sliding fix (due_plan.py `apply_shape_pass` hard_floor, `apply_min_pass` keep) is JUSTIFIED: it implements "--min hard everywhere" in sliding mode (shape pass drained tail days below --min, producing a spurious `min unmet` on a feasible input: 60 cards, min 8, max 16). Ramp stays soft; --min/--max stay hard; no exempt tail reintroduced. Covered by `test_apply_shape_pass_never_drains_a_day_below_its_hard_floor` and the rewritten sliding e2e. Should be recorded as a plan amendment at Record.
- [non-blocking] Case-by-case RED-before-fix for 1.1 was not observed (tests authored with the fix; file fails at import pre-fix). The repro's pre-fix output (4,4,4,4,4,4,4,3,1,0) is independently documented; post-fix verified 3/4 on every day.

Verified: exempt tail fully removed (no `exempt`/`_reached_exempt_tail`/`D6.1` in anki_tools or tests; positive control `apply_min_pass` hits); hard gate `_enforce_hard_bounds` uses live `end_day`; DP-1..DP-4 implemented as decided (later-first then earlier surplus; range upper bound hard even with --set-earlier; histogram marker kept); `--range` LO 0 and `--start-offset` default 0 in both CLIs; `min unmet`/`max unmet` CLI branches precede `apply_moves`. Full suite 2865 passed/17 skipped (run independently, 144s). ruff format/check clean on all 7 touched files; the 2 repo-wide ruff errors and 4 unformatted files are in untouched files (pre-existing).

### Open questions
- None blocking.
