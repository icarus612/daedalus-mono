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
