# code-review

## Round 1 — 08-13-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 5
```

### Verified independently (not just from the exit report)

- `.venv/bin/poetry run pytest`: **106/106 pass** (56 in `test_due_plan.py`, 50 in
  `test_rebalance_due.py`), matching the exit report's claim.
- `ruff check --output-format=concise .` diffed byte-for-byte against
  `.artifacts/baselines/ruff-baseline.txt`: **identical**, still exactly the 11
  pre-existing findings, all in `build_deck.py` / `get_deck_info.py` /
  `mp3_filename_update.py` — none in the new files.
- `flake8 .` diffed byte-for-byte against `.artifacts/baselines/flake8-baseline.txt`:
  **identical**.
- `black --check` on all five new/edited Python files: clean.
- `git diff --stat main...HEAD` (excluding `.venv/`): exactly the 8 files the plan's
  1.1/2.1/3.1 file scopes name — `__init__.py`, `due_plan.py`, `rebalance_due.py`,
  `test_due_plan.py`, `test_rebalance_due.py`, `pyproject.toml`, `poetry.lock`,
  `package.json`. No stray files.
- `.venv/bin/python -c "import anki_tools; ...; anki.buildinfo.version"` prints
  `24.06.3`; `poetry.lock` has `anki` pinned at `24.6.3` (PEP 440 normalization, as the
  plan predicted). File modes on the three `bin`-registered scripts are all `775`,
  consistent with the existing two.
- Read `due_plan.py` end to end against the plan's pseudocode for `apply_max_pass`,
  `apply_reverse_max_pass`, `apply_min_pass`, `plan_rebalance`, and
  `_check_post_conditions`: all five match the plan's algorithm line for line,
  including the subtle bits (shift-cap inclusivity at exactly 14 days, untouched-first
  as primary sort key with `False < True`, `may_move_to` not gating the reverse pass,
  `sink_overflow` computed before the reverse pass but not recomputed after it, the
  `moves` dict keyed off final-day-vs-origin rather than `state.moved`).
- Spot-read the highest-risk tests named explicitly in the plan
  (`test_apply_max_pass_one_day_rule_card_identity`,
  `test_apply_min_pass_keeps_hunting_past_a_cap_blocked_source` — the N17 case,
  the flagship `[0, 40, 2, 0, 25, 1]` `set_earlier=True` scenario in
  `test_due_plan.py`): each asserts on card **identity**, not just counts, exactly as
  the plan insists ("counts alone... don't distinguish the correct behaviour").
- `rebalance_due.py`'s two builder-fixed defects (missing `validate_bounds` wiring;
  missing backup-dir creation) read correctly in the current code — `main()` now
  calls `validate_bounds` before opening the collection and routes `ValueError` into
  `parser.error(...)`; `os.makedirs(backup_dir, exist_ok=True)` precedes
  `col.create_backup(...)`.
- `except DBError` before `except AnkiException` in `main()`'s collection-open block is
  correctly ordered: confirmed in `anki/errors.py` that `DBError(BackendError)` and
  `BackendError(AnkiException)`, so the more specific catch is checked first.
- Order-of-operations safety property (3.2): `plan_rebalance` (pure, zero Anki
  imports) runs to completion — including raising `InfeasibleRebalance` — before any
  backup or `set_due_date` call in `main()`. Confirmed by reading the function, and
  independently by the exit report's own manual dry-run against the *real* collection:
  the default-mode run refused with `InfeasibleRebalance` and produced no histogram,
  exactly as this ordering predicts.

### Findings

- [non-blocking] `anki_tools/rebalance_due.py:36-41` (`resolve_deck_ids`) — the plan's
  3.1 Work section and its "Assumptions I could not verify" section both call for
  echoing the resolved deck name(s) back to the user (`"echo the resolved deck names
  in the error path either way, so a near-miss name is never silently treated as
  absent"`), specifically because `col.decks.id_for_name`'s case-insensitivity is
  *inferred*, not documented, and the plan asked 3.1 to verify it empirically with a
  two-line probe against `"PROGRAMMING::CODING"`. Neither the probe nor the echo is
  present: `resolve_deck_ids` only prints on the not-found path (`No such deck:
  {deck_name!r}`), never confirms the resolved name(s) on the success path, and no
  test resolves an upper/mixed-case deck name. Practical risk is low here (the CLI
  arg is typed as an exact literal and the real invocation in 4.2 used the exact
  case), but this is a plan work-item that was silently dropped rather than
  implemented or explicitly deferred with a reason — worth a follow-up (one print
  statement plus one case-probe test) before this ships as a habitually-run tool.
- [non-blocking] `anki_tools/rebalance_due.py:90-104` (`render_histogram`) — the
  column header reads `"Day offset | Before | After | Note"`, but the values printed
  are the *absolute* day numbers from `RebalanceResult.before`/`after` (same keys as
  `due_plan.py`'s buckets), not an offset from today — `render_histogram` has no
  `today` parameter to compute one (matching the plan's own stated signature, which
  also omits `today` — so this is a latent inconsistency in the plan's own spec
  between "day offset from today" prose and the concrete signature, not purely a
  coding mistake). Confirmed against the exit report's own manual real-collection
  dry-run output, which shows rows like `1808 | 6 | 16` and `2172 | 5 | 5` under a
  "Day offset" header — meaningless numbers to a real user without knowing `today`'s
  absolute day count. Separately, the "below --min" marker is derived independently
  (`after_count < min_per_day`) rather than from `result.short_days`, so it also fires
  on the natural end-of-queue tail day (exempt by definition from `short_days`/D6.1
  reporting), which is what produces the `2172 | 5 | 5 <- below --min` line in the
  evidence — a plausibly non-problem being flagged the same way as a genuine
  cap-induced shortfall. Recommend: either relabel the column (e.g. "Day") or thread
  `today` through and print a true offset; and drive the marker off `result.short_days`
  rather than a raw count comparison so the tail isn't flagged identically to a real
  shortfall.
- [non-blocking] `anki_tools/rebalance_due.py:44-87` (`collect_cards`) — buried cards
  (`queue == -2` or `-3`) fall through to the generic `if not (queue==2 and type==2)`
  branch and are folded into `skip_learning`, so the printed report says "N learning"
  when some of those are actually buried. D1 in the plan lists "new, learning,
  relearning, suspended, buried and filtered-deck cards" as distinct exclusion
  categories. Nothing is silently lost (the total still reconciles), but the label is
  wrong for buried cards specifically. No test exercises a buried card.
- [non-blocking] `anki_tools/due_plan.py:152-206` — `apply_min_pass`'s tail-exemption
  loop (`if all(buckets on later days are empty): break`) and `_short_days`'s copy of
  the same loop are two independent implementations of one rule. They agree today
  (verified by the passing `short_days`-related tests), but nothing enforces they stay
  in sync if either is edited later; consider factoring the tail check into one
  shared helper.
- [non-blocking] `tests/test_rebalance_due.py` — `resolve_deck_ids`'s "nonexistent deck
  names the deck" behavior is unit-tested directly (`test_resolve_deck_ids_nonexistent_deck_raises_naming_the_deck`),
  but no end-to-end test drives `main()`/the CLI through that path to confirm the
  `ValueError` → `print` → `SystemExit(1)` wrapping actually produces a clean exit
  rather than a traceback, as 3.1's acceptance criteria describe. The wrapping is
  simple, but it's the one acceptance-criteria bullet in 3.1 (`"a nonexistent deck
  name produces a non-zero exit with a message naming the deck, not a traceback"`)
  without CLI-level coverage.

### Open questions

None — all findings above are non-blocking notes, not decision points that block a
verdict.

## Round 2 — 08-13-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 1
```

### Verified independently (not just from the exit report)

- `git log --oneline`: rework commit `9ea47dc` sits on top of `4f35f05` on this
  worktree's branch, touching exactly `due_plan.py`, `rebalance_due.py`,
  `test_rebalance_due.py` (`git diff 4f35f05 9ea47dc --stat`) — matches the exit
  report's claimed 3-file round-2 delta exactly.
- `.venv/bin/poetry run pytest -q`: **111/111 pass**, matching the exit report.
- `ruff check --output-format=concise .` and `python3 -m flake8
  --max-line-length=88 .`, both diffed byte-for-byte against
  `.artifacts/baselines/{ruff,flake8}-baseline.txt`: **identical to baseline** —
  still exactly the pre-existing findings, none in the three files this round
  touched.
- `.venv/bin/poetry run black --check` on all four round-1/round-2 Python files:
  clean.
- `~/.claude/hooks/verify-run-scope.sh <worktree> main <run-dir>`: `OK: all 11
  changed files claimed by 1 exit report(s) or harness-owned` — no product change
  in the branch's diff against `main` is unclaimed by lane l1's exit report.
- `git diff --stat main...HEAD`: exactly the same 8 files round 1 was already
  verified against (`__init__.py`, `due_plan.py`, `rebalance_due.py`,
  `test_due_plan.py`, `test_rebalance_due.py`, `pyproject.toml`, `poetry.lock`,
  `package.json`) — no new file entered scope in the rework round.
- Read the full `git diff 4f35f05 9ea47dc` for `due_plan.py` and `rebalance_due.py`
  line by line against each of round 1's five non-blocking findings:
  - **Finding 1** (deck-name echo) — `resolve_deck_ids` now does
    `resolved_names = [col.decks.name(did) for did in child_ids]` and prints
    `Resolved deck(s): {...}` on the success path. New tests
    `test_resolve_deck_ids_is_case_insensitive` and
    `test_resolve_deck_ids_echoes_resolved_names_on_success` cover exactly the
    empirical case-insensitivity probe and the echo the plan asked for. Both pass.
  - **Finding 2** (absolute day vs. offset; raw-count vs. `short_days` marker) —
    `render_histogram` gained `today`/`short_days` params; the row value is now
    `day - today`, and the below-`--min` marker is `day in short_days_set` instead
    of `after_count < min_per_day`. All 6 pre-existing call sites (5 in tests, 1 in
    `main()`) were updated to the new 6-arg signature — confirmed via `grep -rn
    "render_histogram("` across `anki_tools/` and `tests/`, no stale 4-arg call
    left. New tests directly exercise both the offset math
    (`test_render_histogram_row_shows_small_offset_not_large_absolute_day`, with
    `today=1800, day=1805` asserting `"1805"` never appears and `"5"` does) and the
    tail-exemption fix
    (`test_render_histogram_day_not_in_short_days_never_marked_below_min`, a
    zero-count day *not* in `short_days` correctly unmarked). All pass.
  - **Finding 3** (buried cards mislabeled "learning") — `collect_cards` now checks
    `card.queue in (-2, -3)` immediately after the suspended check, before the
    new/learning checks, incrementing a dedicated `skip_buried` counter; the
    skip-report print statement names "buried" as its own field. New test extends
    `test_collect_cards_filters_to_review_queue_due_on_or_after_start` with both a
    user-buried (`queue=-2`) and scheduler-buried (`queue=-3`) card, asserts
    neither is returned, asserts `"buried"` appears in captured stdout, and updates
    the arithmetic-identity total from 6 to 8. Passes.
  - **Finding 4** (duplicated tail-exemption loop) — new `_reached_exempt_tail(state,
    d)` helper, byte-identical in logic to the two inline loops it replaces (same
    `all(len(buckets.get(day, [])) == 0 for day in range(d+1, end_day+1))`
    predicate), called from both `apply_min_pass` and `_short_days`. `grep -c` shows
    exactly one remaining inline occurrence (inside the helper itself) and two call
    sites. The refactor is a pure extraction — no logic changed — corroborated by
    all 56 `test_due_plan.py` tests (untouched by this round) passing unchanged.
  - **Finding 5** (no CLI-level e2e test for the nonexistent-deck path) — new
    `test_e2e_nonexistent_deck_exits_nonzero_naming_the_deck_not_a_traceback` drives
    `main()` through `_run_cli` with an invalid deck name and both `--min`/`--max`
    supplied (isolating the deck-resolution path from the already-covered
    bounds-validation path), asserting non-zero exit and the deck name in stdout.
    Passes; `_run_cli` only catches `SystemExit`, so an unhandled exception of any
    other type would have failed the test with an error rather than a clean
    assertion, which is itself part of what the test proves.
  All five round-1 findings are fixed as described, each with a fix-specific
  regression test, none merely asserted away.
- Read the incident narrative in the exit report (a sub-agent's stray `git checkout
  --` briefly reverted a sibling's uncommitted findings 1–3 work) against the final
  artifacts: `git status --porcelain` in the worktree shows a clean tree aside from
  the (expected, uncommitted) plan directory; the final commit's diff contains all
  three findings' fixes intact and matches the byte-identical-recovery claim. No
  residual data loss from the incident is visible in the shipped code.

### Findings

- [non-blocking] `anki_tools/rebalance_due.py:95` (`render_histogram`) — the
  finding-2 fix switched the below-`--min` marker from a raw
  `min_per_day`/`after_count` comparison to `day in short_days_set`, but the
  `min_per_day` parameter was left in the function signature and is no longer
  referenced anywhere in the function body (confirmed via `grep -n "min_per_day"
  anki_tools/rebalance_due.py` — only the `def` line and the unchanged call site
  in `main()` remain). Harmless (neither `ruff` nor `flake8` flag unused
  parameters by default, consistent with the clean lint diff), but it's dead
  signature surface left over from this round's fix; worth dropping the parameter
  (and updating the one call site plus the handful of test call sites) in a future
  pass rather than carrying an argument nothing reads.

### Open questions

None — the one finding above is a cosmetic follow-up, not a decision point.

## Round 3 — 08-14-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 2
```

Scope: Phase 6 only (commit `98a90ae`, 7 files, +2900/-102 — `due_plan.py`,
`due_stats.py` new, `rebalance_due.py`, `package.json`, `test_due_plan.py`,
`test_due_stats.py`, `test_rebalance_due.py`). Phases 1-5 already gated
twice and are not re-litigated here. Fresh isolated context; verified
against the plan's subphases 6.1-6.6 and the settled table (D1-D9,
DP-A..DP-F) by reading the real code and re-running every check, not from
the exit report's claims alone.

### Verified independently (not just from the exit report)

- `.venv/bin/poetry run pytest -q`: **189/189 pass** (97 `test_due_plan.py`
  + 74 `test_rebalance_due.py` + 18 `test_due_stats.py`), matching the exit
  report.
- `ruff check --output-format=concise .` and
  `python3 -m flake8 --max-line-length=88 .`, both diffed byte-for-byte
  against `.artifacts/baselines/{ruff,flake8}-baseline.txt` from the
  package root: **identical to baseline** — zero new findings in any of the
  three Phase 6 files.
- **Default-mode regression, re-derived independently rather than trusted.**
  Wrote a standalone script reproducing `gen_pre_phase6_baselines.py`'s
  exact three fixtures (F1 feasible-flat, F2 reverse-pass, F3 cap-blocked)
  against the **current, post-Phase-6** `due_plan.plan_rebalance`, and
  diffed the resulting `{card_id: new_day}` maps against
  `.artifacts/pre-phase6/moves-{F1,F2,F3}.json` byte-for-byte in Python
  (dict equality, not just JSON text): **F1/F2/F3 all MATCH.**
- **DP-B / hard-vs-shape split is real in code, not just by convention.**
  Read `check_hard_feasibility`, `analyze_shape`, and the shared
  `window_violations` kernel in `due_plan.py:554-808` line by line:
  `check_hard_feasibility` never receives or constructs a `DayTargets` line
  at all — its only capacity source, in all three checks (global upper,
  global lower, window/Hall), is `constant_targets(..., max_per_day)` or
  the raw scalar `max_per_day`/`min_per_day`. `analyze_shape` is the only
  caller that passes the `target` (`T(d)`) line into `window_violations`,
  and its result (`ShapeAnalysis`) has no `feasible` field at all —
  `check_feasibility` composes `feasible=hard.feasible` only, never mixing
  in `shape.shape_reachable`. The split is structural (no code path can
  accidentally feed `T(d)` into the hard gate), not merely tested-around.
  Corroborated by `test_dp_b_dp_f_boundary_cap_unreachable_but_max_feasible_passes_the_hard_gate`
  and `test_check_hard_feasibility_uncapped_matches_the_6_1_prefix_condition`
  (both pass), which reproduce the plan's own real-block numbers (1360
  cards / 980 capacity / gap 380 at shift 14; minimum feasible shift 48)
  exactly.
- **DP-B hard-fails both sides, `--set-earlier` downgrades only upper/window
  to warnings, lower bound is unconditional.** Confirmed in
  `check_hard_feasibility` (`due_plan.py:644-673`): the lower-bound branch
  never checks `set_earlier`; the upper-bound and window branches do,
  appending a "downgraded to warning" message and leaving `feasible=True`
  when `set_earlier` is set. Matches 6.1 point 4 exactly.
- **DP-F best-effort default confirmed in `plan_rebalance`'s sliding block**
  (`due_plan.py:432-455`): `apply_shape_pass` + `apply_min_pass(state,
  target)` run unconditionally, `over_target_days` is always computed and
  returned, and `InfeasibleRebalance` is raised **only** when
  `strict_sliding and over_target_days` — never on shape alone by default.
  `test_sliding_cap_blocked_reports_over_target_days_without_raising` and
  `test_strict_sliding_raises_on_the_same_cap_blocked_case` (both pass)
  exercise exactly this branch.
- **Two-stage sliding sequence provably cannot breach `max_per_day`, traced
  by hand.** `plan_rebalance` runs the hard max pass (and reverse pass if
  needed) to completion — raising if still over cap — *before* the sliding
  block ever executes. `apply_shape_pass` only moves a card into `d-1` when
  `len(buckets[d-1]) < hard_ceiling[d-1]` (`due_plan.py:242-243`), so the
  receiver can never be pushed over `max_per_day`, including at `start_day`.
  `apply_min_pass(state, target)` only fills a day up to `target[d]`, and
  `target[d] <= max_per_day` everywhere by `build_target_line`'s
  construction (descends from `max_per_day` to `min_per_day`), so it can
  never push a day above the hard cap either. Confirmed by
  `test_apply_shape_pass_never_breaches_the_hard_ceiling` (parametrized) and
  `test_two_stage_necessity_flat_cap_prevents_sink_overflow_shape_alone_would_cause`,
  which also asserts the naive single-stage substitution the plan forbids
  *does* break the sink — proving the two-stage order is load-bearing, not
  stylistic. Both pass.
- **`--range` containment, both directions, traced by hand.** Downward:
  `may_move_to` refuses any `target_day < state.start_day` unconditionally
  (unchanged from Phase 2), and `state.start_day == LO` in range mode — so
  the shift-cap budget can never reach below `LO`
  (`test_plan_rebalance_range_mode_shift_cap_clamped_by_start_day_floor`
  passes). Upward: `may_move_later_to` gates every placement in
  `apply_reverse_max_pass` (`due_plan.py:190`) and refuses once
  `target_day > state.max_end_day`; on refusal the pass leaves the excess in
  place and does **not** create a bucket past the ceiling, so
  `state.end_day` never exceeds `max_end_day` in range mode — the existing
  `over_max`/`InfeasibleRebalance` path (no new exception type) then catches
  it, exactly as 6.2 specifies
  (`test_plan_rebalance_range_mode_upward_containment_raises_infeasible_not_new_type`
  passes). Confirmed no horizon extension in range mode: `move_card` still
  updates `state.end_day = max(state.end_day, to_day)`, but nothing ever
  calls it with a `to_day` past `max_end_day` because `may_move_later_to`
  gates the call site first.
- **Backup ordering, read directly in `rebalance_due.py:main()`
  (lines 390-430).** Exact sequence: `collect_cards` -> `check_feasibility`
  -> (fail: `_print_infeasibility` + `SystemExit(1)`, no backup, no
  `plan_rebalance` call) -> (pass) backup block -> `plan_rebalance` -> (in
  `finally`, after confirmation) `apply_moves`. A failed precheck exits
  before the backup block is ever reached. Corroborated by
  `test_e2e_precheck_failure_creates_no_backup_and_collection_untouched` and
  `test_e2e_infeasible_rebalance_after_precheck_creates_backup_untouched_collection`
  (both pass, both assert on backup-directory contents, not just exit code).
- **The two self-reported redispatch defects are both present and correct
  in the shipped code.** (1) `apply_reverse_max_pass`'s `ceiling.get(d,
  ceiling[state.start_day])` fallback (`due_plan.py:189`) — reproduced the
  original `KeyError` scenario by hand against a from-scratch script
  (50 cards on day 1, `max_per_day=16`, `set_earlier=True`, no `--range`)
  against a copy of the pre-fix logic; confirmed the shipped fallback
  handles it. (2) `_print_infeasibility`'s `suggested_min == 0` branch
  (`rebalance_due.py:323-329`) — independently re-derived the plan's own
  worked example (30 cards spread across a 365-day horizon, one card
  pinned to day 365 so the horizon actually resolves to 365) via
  `check_feasibility` directly: `feasible=False`, `suggested_min=0`
  exactly as the plan requires, and traced the print path to confirm it
  emits the "omit --min entirely, or narrow the window with --range"
  guidance rather than the literal `Suggested --min: 0` the plan
  specifically forbids.
- **The "pre-existing, left unfixed" cosmetic bug is genuinely
  pre-existing.** `grep` confirms `.artifacts/pre-phase6/rebalance_due.py`
  (the verbatim pre-Phase-6 copy) already prints `result.short_days` as raw
  absolute day numbers at the same call site — this predates the round and
  is correctly out of the plan's 6.1(d) scope (which names exactly two
  cosmetic fixes: the "was extended" mislabel and `render_histogram`'s dead
  parameter). Not a regression.
- `due_stats.py`: mode 755, shebang-first, registered in `package.json`
  `bin` as `anki-due-stats`, no `except Exception`/`# noqa` anywhere across
  the three Phase 6 source files (`grep` confirms). Never calls
  `create_backup` or `set_due_date`; `test_mtime_unchanged_after_run`
  passes.
- `git show --stat 98a90ae` and `git diff --stat main...HEAD -- libs/python/anki-tools/`
  agree: this round's commit touches exactly the 7 files its own file
  scopes name (5 edited + 2 new); no `pyproject.toml`/`poetry.lock` churn,
  consistent with no new runtime dependency being needed for Phase 6.

### Findings

- [non-blocking] `anki_tools/due_plan.py:285-288` (`_infeasible_reason`) —
  self-reported by the exit report and independently confirmed: a
  range-mode reverse-pass refusal caused by `may_move_later_to` (the
  containment ceiling) and a genuine `--max-shift` refusal both surface as
  the same `"shift cap"` reason string on `InfeasibleRebalance`, because
  `_infeasible_reason` only distinguishes `start_day` (sink overflow) from
  everything else. The plan's 6.2 acceptance criteria only require the
  *existing* exception type and the offending days (both satisfied), not a
  distinct label, so this is not a spec violation — but a user hitting a
  `--range`-clamped reverse pass sees "shift cap" in the error text with no
  mention of `--range`, which could send them toward raising `--max-shift`
  (which cannot help) instead of widening `--range` (which would). Worth a
  follow-up to add a third reason value once there's a call site that can
  distinguish the two causes.
- [non-blocking] Test coverage gap on the `suggested_min == 0` wording fix
  (defect 2 above): no pytest exercises `_print_infeasibility`'s
  `suggested_min == 0` branch specifically — the closest e2e precheck-failure
  test (`test_e2e_precheck_failure_creates_no_backup_and_collection_untouched`,
  3 cards / 3 days / `--min 8`) lands on `suggested_min == 1`, not `0`, so it
  never reaches the special-cased wording. The fix is correct (verified
  independently above) and was checked manually against a real collection
  per the exit report, but there is no regression test pinning the exact
  "omit --min entirely, or narrow the window" string for the zero case, so
  a future refactor of `_print_infeasibility` could silently reintroduce
  the bare `Suggested --min: 0` wording the plan forbids without any test
  failing.

### Open questions

None — both findings above are non-blocking notes, not decision points
that block a verdict.
