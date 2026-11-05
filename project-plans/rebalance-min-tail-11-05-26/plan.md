# rebalance-min-tail — make `--min` a hard bound in `anki-rebalance-due`

### Ask of record

**11-05-26** — "the rebalancing tool should take in a min.... if it shows values of 1 and 0 MIN ISNT FUCKING WORKING AND YOU SHOULD REPORT AND FIX THAT"

**11-05-26 — appended** — "TODAY INCLUDED! i said from today"

**11-05-26 — appended** — "i never once said to give it an exempt tail rule, and even REPEATEDLY said NOT to do that... it should fucking fail if the range cant be met... which again... i said repeatedly"

**11-05-26 — appended** — "ok range max and min make sense but FUCKING FIX THEM"

Context: repro on deck "Languages::Russian::4. Sentences (lingo llama)": `--range 1-10 --min 3 --max 4 --set-earlier --dry-run` produced per-day 4,4,4,4,4,4,4,3,1,0 with no warning.

**11-05-26 — appended, window semantics** — "no range is correct not fucking days. it should be able to go from days other than starting at today every time, hense the fucking name. 0 is today (default) and it should take in a start and stop day"

## Phase syllabus
- [ ] Phase 1: Regression tests
  - [ ] 1.1: Failing regression tests for the min tail, hard min failure, and today-inclusive window
- [ ] Phase 2: Planner core (`due_plan.py`)
  - [ ] 2.1: Delete the exempt tail, borrow-later min pass, hard-bounds gate  (after: 1.1)
  - [ ] 2.2: Feasibility precheck agrees with the planner on `--min`  (after: 2.1)
- [ ] Phase 3: CLI window and messaging
  - [ ] 3.1: Day 0 = today: `--range` LO >= 0 and `--start-offset` default 0 in both CLIs  (after: 1.1)
  - [ ] 3.2: `rebalance_due` reports `min unmet` / `max unmet` and drops the dead flat short-day line  (after: 2.1, 3.1)
- [ ] Phase 4: Existing tests rewritten to the new behaviour
  - [ ] 4.1: Rewrite every test that pins the exempt tail, the soft min, or the start-offset-1 default  (after: 2.2, 3.2)
- [ ] Phase 5: Verify
  - [ ] 5.1: Full suite, lint, and the repro shape  (after: 4.1)

## Goal & scope

**Goal.** `--min` is a hard per-day bound on every day of the rebalance window, exactly like `--max`. A run that cannot put every day in `[--min, --max]` raises `InfeasibleRebalance` and the CLI writes nothing to the collection. With `--set-earlier`, the min pass may move surplus cards *later* so feasible inputs actually reach the floor. Day offset 0 is today and is the default window start; `--range START-STOP` accepts any start >= 0.

**In scope** (the coordinator's brief, required behaviour 1-5, plus the window-semantics amendment):

1. Delete the exempt-tail rule entirely (`_reached_exempt_tail`, due_plan.py:542-549, and both of its callers `apply_min_pass` 552-574 and `_short_days` 720-729) in every mode: flat, sliding, with or without `--range`.
2. After all passes, any day in `[start_day, state.end_day]` below `--min` or above `--max` raises `InfeasibleRebalance` (new reasons `"min unmet"` / `"max unmet"`); the CLI prints and exits non-zero before `apply_moves`. No best-effort, no silently short days. In sliding mode the ramp target stays soft; `--min`/`--max` stay hard.
3. With `--set-earlier`, the min pass may borrow surplus cards (above the source day's own floor) from earlier days and move them later, respecting sibling separation and the range/horizon ceiling. Post-conditions treat these as sanctioned later moves.
4. `--range` accepts LO = 0 (window starts today; cards due today included; overdue still excluded). `parse_range` is shared with `due_stats.py`.
5. The feasibility precheck agrees with the planner: precheck-feasible means the plan meets `--min`/`--max` or the plan raises; precheck-infeasible means no plan exists.
6. (Amendment) `--start-offset` default changes from 1 to 0 in BOTH `anki-rebalance-due` and `anki-due-stats`; help text and `parse_range` error messages updated. `--range START-STOP` stays the window flag; no `--days` or any other new window flag.

**Out of scope** (explicitly):
- No new window flag (`--days` etc.) — forbidden by the amendment.
- No change to max-side planning (`apply_max_pass`, `apply_reverse_max_pass`) or separation repair semantics, beyond the precheck tightening in 2.2.
- No exact (flow/matching-based) planner — see DP-1.
- No change to the skip-report wording "already due or overdue" for cards between today and a positive `--range` LO (pre-existing imprecision; follow-up candidate).
- No validation of negative `--start-offset` (pre-existing; follow-up candidate).
- Docs are NOT edited by any build subphase — the Record stage (`documenter` / `document-local`) updates them (see Skill mapping).

Acceptance (from the brief): the repro shape — 32 cards distributed 9,6,5,5,3,2,0,0,1,1 over days 1-10, `--min 3 --max 4 --set-earlier`, range 1-10 — yields every day in [3,4]; an infeasible `--min` raises and writes nothing. Planner-observed: a throwaway experiment in the planner's scratchpad (not product code) with exempt-tail removed plus an earlier-borrow min pass produced `[4, 4, 3, 3, 3, 3, 3, 3, 3, 3]` for the repro shape, so the acceptance figure is reachable by the design in 2.1.

## Stack & MAJOR versions

- Python `>=3.11` — `libs/python/anki-tools/pyproject.toml` (`requires-python`). Idioms already in use: PEP 604 unions (`int | None`), `collections.abc`, frozen dataclasses (due_plan.py).
- `anki` (unpinned in `pyproject.toml`; resolved by uv's lockfile) — only `rebalance_due.py`/`due_stats.py` and e2e tests import it; `due_plan.py` is Anki-free by design (due_plan.py:1-7).
- pytest (dev group, `pyproject.toml` `[dependency-groups] dev`), `testpaths = ["tests"]`.
- Runner: `uv run --group dev pytest` (libs/bash/build-tools/py-scripts/py-test); lint: `uv run ruff format --check .` then `uv run ruff check .` (py-scripts/py-lint). Package scripts in `libs/python/anki-tools/package.json` (`pnpm --filter lib.python.anki-tools test|lint`).
- Baseline observed by the planner: the six rebalance-related test files (`test_due_plan.py`, `test_rebalance_due.py`, `test_due_stats.py`, `test_followup_fixes.py`, `test_min_separation_e2e.py`, `test_separation_repair_e2e.py`) — 261 passed on this branch at plan time.

## Conventions to enforce (hard constraints)

- `due_plan.py` stays pure: no Anki imports, no collection access (module docstring, due_plan.py:1-7).
- Determinism: every move-order decision goes through `max_move_order` / `min_move_order` (seeded tie, due_plan.py:156-202); new code must not introduce unseeded randomness or dict/set iteration-order dependence.
- Every move goes through `move_card` (keeps `day_by_id`, `moved`, `end_day` live, due_plan.py:484-493). Every placement checks `separation_ok`; earlier placements via `may_move_to`, later placements via `may_move_later_to` (due_plan.py:228-252).
- **Delete old code when replacing it** — no exempt-tail remnant, no flag to re-enable it, no compatibility path, no versioned names (user CLAUDE.md; the brief: "do not soften, scope, or keep variants").
- **Minimal code comments** (`~/.claude/rules/minimal-code-comments.md`): no banners, no narration, tests included. Rewritten tests drop their old exempt-tail narration (e.g. test_rebalance_due.py:656-660, 2100-2113) rather than replacing it with new essays. Rationale goes in docs at Record.
- Tests: each e2e file keeps its own local `_add_card` / `_run_cli` / `_snapshot_due_ivl` helpers (pattern: tests/test_min_separation_e2e.py, tests/test_separation_repair_e2e.py); pure-core tests use `cards_from_counts` / `state_from_counts` / `make_state` from tests/test_due_plan.py. No test opens the user's real collection.
- Existing tests that encode the old behaviour are REWRITTEN to the new behaviour, never deleted silently. A rename to state the new behaviour is fine; a deletion must be named in the exit report with its replacement.
- Ruff format + ruff check clean (py-lint). All hooks green.
- Git: no `git checkout`/`git stash`/`git reset` or any other git state command inside the lane beyond the builder's own commits (user memory: a lane once reverted sibling edits as "lint collateral"). No attribution trailers of any kind — no `Co-Authored-By`, no `Claude-Session`, no session URL in any commit. Work lands by local merge into `main`; no PR (repo CLAUDE.md).

## Phase 1: Regression tests

### 1.1: Failing regression tests for the min tail, hard min failure, and today-inclusive window

- **File scope:** `libs/python/anki-tools/tests/test_rebalance_min_hard.py` (new).
- **Pattern to follow:** pure-core cases like `test_plan_rebalance_flagship_trace_requires_set_earlier_true` (tests/test_due_plan.py:741-771; build cards by per-day counts — copy a small local `cards_from_counts` or import it from `tests.test_due_plan` only if that import already works in this suite; prefer a local helper). E2E cases like tests/test_min_separation_e2e.py (local `_add_card`, `_run_cli`, `_snapshot_due_ivl`, scratch `Collection` under `tmp_path`).
- **Reproduction (exact):** pure core — `plan_rebalance(cards, start_day=1, min_per_day=3, max_per_day=4, max_shift=14, set_earlier=True, end_day=10)` with 32 cards at per-day counts `[9, 6, 5, 5, 3, 2, 0, 0, 1, 1]` over days 1-10. Observed today: `after` = 4,4,4,4,4,4,4,3,1,0 (the user's repro; matches the cause — `_reached_exempt_tail` breaks the min pass at day 9, and `apply_min_pass` only searches later days, due_plan.py:552-574). Expected: every day 1-10 holds 3 or 4 cards, sum 32.
- **Cases (each must be observed RED before any fix subphase runs):**
  1. Repro shape above → every day in [3, 4]; `result.short_days == []`.
  2. Infeasible min, pure core: e.g. counts `[8, 3]`, `min_per_day=8`, `max_per_day=None`, `set_earlier=False` (today this is the shape `test_apply_min_pass_exempts_the_trailing_days` treats as legal) → `InfeasibleRebalance` with `exc.reason == "min unmet"` and `2 in exc.days`.
  3. Cap-induced shortfall now raises: counts `[0, 20]`, `min_per_day=8`, `max_shift=0` (the shape of `test_plan_rebalance_cap_induced_shortfall_is_reported_not_raised`, test_due_plan.py:808-815) → raises `"min unmet"`.
  4. Sliding: `--min`/`--max` hard in sliding mode — a sliding input whose ramp is reachable but whose last day would end below `--min` without the hard pass (derive the fixture from the old sliding e2e shape, test_rebalance_due.py:2094-2146: 60 cards, 10/day over 6 days, min 8 max 16) → either every day in [8, 16] or `InfeasibleRebalance("min unmet")`; never a returned result with a day below 8.
  5. `parse_range("0-10") == (0, 10)` and `parse_range("0") == (0, 0)`; `parse_range("-1-5")` still raises `ValueError` (via the malformed path: `split("-", 1)` leaves an empty start string, rebalance_due.py:63-72).
  6. `build_parser()` default `start_offset == 0` for both `anki_tools.rebalance_due` and `anki_tools.due_stats`.
  7. E2E apply: scratch collection with the repro shape placed at day offsets 1-10 (ivl varied), run `--range 1-10 --min 3 --max 4 --set-earlier --yes --no-backup` → exit 0, every day offset 1-10 holds 3 or 4 cards on re-open.
  8. E2E infeasible: a shape that fails `--min` only inside the planner (not the precheck — e.g. one that is blocked by `--max-shift 0`) → exit non-zero, `_snapshot_due_ivl` identical before and after. Plus a shape that the precheck rejects → exit non-zero, unchanged.
  9. E2E today-inclusive: a card due today (offset 0) and an overdue card (offset -1) with `--range 0-3` → the today card is in scope (appears in the histogram at offset 0 / may move), the overdue card is skipped and untouched. Same with no `--range` (default window start 0).
- **Acceptance:** file exists, cases 1-9 fail on the unfixed code for the stated reason (record the failing assertion per case in the exit report), no other test file touched.
- **Test oracle:** new contract tests.

## Phase 2: Planner core (`due_plan.py`)

### 2.1: Delete the exempt tail, borrow-later min pass, hard-bounds gate

- **File scope:** `libs/python/anki-tools/anki_tools/due_plan.py` only.
- **Pattern to follow:** `apply_reverse_max_pass` (due_plan.py:520-539) for later-direction moves gated by `_resolve_later_target` / `may_move_later_to`; `apply_separation_repair_pass` (392-429) for returning a "moved later" flag that feeds `later_move_used` (908); `_days_over_max` (672-677) for the gate's day scan.
- **Changes:**
  1. Delete `_reached_exempt_tail` and both call sites. `_short_days` keeps reporting days below the floor it is handed, over the whole window.
  2. `apply_min_pass(state, floor, set_earlier)` returns `bool` (any later move made). Per deficit card for day `d`: first the existing later-source search unchanged (sources `d+1..end_day`, `min_move_order`, `may_move_to`). Only if that finds nothing AND `set_earlier`: search earlier sources `s = d-1` down to `state.start_day` (nearest first, so displacement is smallest), skipping any `s` with `len(buckets[s]) <= floor[s]`; within a source use `max_move_order` (largest-ivl first, same as every other "move off a day" choice); a candidate is legal iff `may_move_later_to(d, state)` and `separation_ok(cid, d, state)`. Move via `move_card`. Without `set_earlier` no card ever moves later (post-condition, due_plan.py:771-776, stays).
  3. `plan_rebalance`: flat branch calls `apply_min_pass(state, min_floor, set_earlier)`; sliding branch calls it with `target` (soft) and then again with `constant_targets(..., min_per_day)` (hard), so the hard floor can borrow from surplus above `--min` rather than above the ramp. OR the returned flags into `later_move_used` before `_check_post_conditions`.
  4. New hard-bounds gate after the min passes, before `moves` is computed: scan `[state.start_day, state.end_day]` using the LIVE `state.end_day` at gate time, never a pre-pass snapshot or a recomputed latest-occupied day — `move_card` only ever grows `end_day` (due_plan.py:488), so the window the gate checks is the original latest card day or later and an emptied tail can never fall out of it; any day `< min_per_day` → `InfeasibleRebalance(days, counts, "min unmet")`; else any day `> max_per_day` → `InfeasibleRebalance(days, counts, "max unmet")`. Implement as a small pure helper (e.g. `_enforce_hard_bounds(state, min_per_day, max_per_day)`) so the max branch, unreachable through `plan_rebalance` today, is unit-testable on a hand-built `RunState`. Remove the now-redundant max-per-day loop in `_check_post_conditions` (783-788).
  5. `InfeasibleRebalance.__init__` message names the right bound: `--min` for `"min unmet"`, `--max` otherwise. Update its docstring (79-97) and `RebalanceResult.short_days`'s field comment (74: "excluding the exempt tail") to the new meaning: flat mode is always `[]` on return; sliding mode lists days under the soft ramp target.
  6. Module docstring and the `apply_shape_pass` docstring ("sliding mode is already documented as best-effort") — keep the ramp best-effort wording, add nothing that implies `--min` is soft.
- **Acceptance:** 1.1 cases 1-4 green; no reference to `exempt` / `_reached_exempt_tail` / `D6.1` left in `anki_tools/` (grep with a positive control: the same grep finds `apply_min_pass`); `set_earlier=False` runs never move a card later.
- **Test oracle:** existing suite (1.1 regression tests go green; the existing-suite reds caused by intended behaviour change are 4.1's job). Add to `test_rebalance_min_hard.py`: a direct unit test of the gate helper's `"max unmet"` branch and of `apply_min_pass` borrowing (earlier source surplus above floor only; separation-blocked candidate skipped; `max_end_day` respected) — new contract tests for the added behaviour.

### 2.2: Feasibility precheck agrees with the planner on `--min`

- **File scope:** `libs/python/anki-tools/anki_tools/due_plan.py` (precheck section, 968-1303), `libs/python/anki-tools/tests/test_rebalance_min_hard.py` (agreement tests appended).
- **Pattern to follow:** `window_violations` (1034-1076) — prefix sums over origin counts, O(D²) windows; `check_hard_feasibility`'s violation-string + `feasible=False` style (1113-1166).
- **Changes:**
  1. Add a min-side Hall-style necessary condition. For window `[a, b]` the demand is `(b - a + 1) * min_per_day`; the supply is the number of cards whose legal landing range intersects `[a, b]`: origins in `[lo, hi]` with `hi = b + max_shift` (or `end_day` when `max_shift is None`), clamped to the window end, and `lo = a` without `--set-earlier` (cards only move earlier) or `lo = start_day` with it (cards may move later within the ceiling). Any window with supply < demand is a hard violation (not downgraded by `--set-earlier`), reported like the max-side window message (offset-labelled via `day_offset_base`). The existing global lower bound (1130-1138) stays.
  2. Under an explicit range (`end_day is not None`) the global upper bound is a hard violation even with `--set-earlier` — the reverse pass cannot extend past `max_end_day` (due_plan.py:248-249), so today's downgrade (1121-1125) is a precheck/planner disagreement. Without a range the downgrade stays. (See DP-3.)
  3. `suggested_min` (1183) becomes the largest `m` in `[0, total // horizon_days]` for which the min-side conditions pass (monotone in `m`; linear or bisect), so the suggestion is itself precheck-feasible. `due_stats._print_feasible_ranges` (due_stats.py:121-139) reads it unchanged.
- **Acceptance:** agreement test: a seeded grid of small random inputs (pure core; varied counts, `min`/`max`, `max_shift` in {0, 2, None}, `set_earlier` both, with and without `end_day`) asserts (a) precheck infeasible ⇒ `plan_rebalance` raises `InfeasibleRebalance`; (b) `plan_rebalance` returns ⇒ every day in `[start_day, result.end_day]` is within `[min, max]`. Cases where the precheck says feasible and the planner raises are allowed by requirement 5 but must be counted and printed in the test failure message only if (a) or (b) breaks. The repro shape is precheck-feasible with `--set-earlier` and infeasible without it (planner-observed: `check_feasibility(..., set_earlier=False).feasible is False`, caught today by the max-side prefix window).
- **Test oracle:** new contract tests (agreement property) + existing suite.

## Phase 3: CLI window and messaging

### 3.1: Day 0 = today: `--range` LO >= 0 and `--start-offset` default 0 in both CLIs

- **File scope:** `libs/python/anki-tools/anki_tools/rebalance_due.py` (`parse_range` 54-78, `--start-offset`/`--range` help 355-378), `libs/python/anki-tools/anki_tools/due_stats.py` (`--start-offset`/`--range` help 81-102, module docstring line 5 if it states the default).
- **Pattern to follow:** existing `parse_range` error style — one distinct `ValueError` message per failure mode (pinned by `test_e2e_range_invalid_forms_each_get_a_distinct_message`, test_rebalance_due.py:1736-1760).
- **Changes:** DELETE the `lo < 1` branch (rebalance_due.py:74-75) outright, with no replacement lower-bound check. It cannot be relaxed to `lo < 0`: `text.split("-", 1)` (63-64) turns any leading `-` (e.g. `-1-30`) into an empty start string, so `int("")` raises and the input gets the malformed message — no input can reach `parse_range` with a negative start, and a `lo < 0` branch would be dead code (plan-review round 1, gate decision). Two failure modes remain: malformed, and HI < LO; their messages stay distinct. Docstring: lists those two failure modes and states that day offset 0 is today; any start >= 0 is accepted. `--start-offset` `default=0` in both parsers; help says day offset 0 is today and is the default, cards due today are included, overdue cards (due before today) are never touched. No new flag. `collect_cards` needs no change: `card.due < start_day` already excludes overdue when `start_day == today` (rebalance_due.py:161-163); `apply_moves` already writes offset strings relative to today (221-229), so offset 0 is valid.
- **Acceptance:** 1.1 cases 5, 6, 9 green.
- **Test oracle:** existing suite (1.1 contracts).

### 3.2: `rebalance_due` reports `min unmet` / `max unmet` and drops the dead flat short-day line

- **File scope:** `libs/python/anki-tools/anki_tools/rebalance_due.py` (`main`, 555-660).
- **Pattern to follow:** the existing `except InfeasibleRebalance` reason ladder (569-588).
- **Changes:** add a branch for `"min unmet"` (advice: lower `--min`, pass `--set-earlier` so surplus may move later, raise `--max-shift`, or narrow/shift `--range`) and `"max unmet"`; the final `else` stays the `--strict-sliding` message. Delete the flat-mode label `"Days still below --min after the shift cap"` (617) — flat `short_days` is always empty after 2.1; the sliding "under the ramp target" line stays. The sliding NOTE (638-656) already says `--min/--max` "ARE enforced exactly" — now true; keep. Raising happens before `apply_moves` (673), so nothing is written to the collection.
- **Acceptance:** 1.1 cases 7-8 green; output on `min unmet` names `--min` and the offending day offsets.
- **Test oracle:** existing suite (1.1 contracts).

## Phase 4: Existing tests rewritten to the new behaviour

### 4.1: Rewrite every test that pins the exempt tail, the soft min, or the start-offset-1 default

- **File scope:** `libs/python/anki-tools/tests/test_due_plan.py`, `tests/test_rebalance_due.py`, `tests/test_due_stats.py`, `tests/test_followup_fixes.py`, `tests/test_min_separation_e2e.py`, `tests/test_separation_repair_e2e.py`.
- **Method:** run the full suite after 2.1-3.2; every red test is classified in the exit report as (a) pins removed behaviour → rewrite its assertion to the new contract (raise `"min unmet"`, or every day in bounds), keeping its original intent where that intent survives (e.g. a separation test keeps testing separation — change its fixture so `--min` is satisfiable, or drop `--min` from a test that is not about min); (b) fixture relied on window start = tomorrow → pass `--start-offset 1` / `--range 1-N` explicitly or move fixture days; (c) genuine regression → stop and fix the product code, not the test.
- **Known set (planner-observed by a throwaway experiment in its scratchpad with the exempt tail removed, a min-unmet gate, an earlier-borrow min pass, and `start_offset=0`; indicative, not exhaustive — the run, not this list, is authoritative):**
  - test_due_plan.py: `test_apply_min_pass_exempts_the_trailing_days` (592, named in the brief — rewrite to "min pass leaves day 2 short; `plan_rebalance` raises `min unmet`", rename), `test_plan_rebalance_flagship_trace_requires_set_earlier_true` (741; pins `[16,16,10,9,16,1]` with min 8 and `short_days == []` — the bug itself; experiment gave `[16,16,10,9,9,8]`), `test_plan_rebalance_cap_induced_shortfall_is_reported_not_raised` (808), `test_flat_mode_is_bit_identical_through_the_shared_daytargets_path`, `test_sliding_cap_blocked_reports_over_target_days_without_raising`, `test_plan_rebalance_actively_repairs_pre_existing_violations_untouched_by_load`, `test_plan_rebalance_honours_max_after_repair_with_genuine_overflow_pressure`, `test_plan_rebalance_reproducible_with_active_separation_repair`, `test_plan_rebalance_omitting_horizon_ceiling_is_backward_compatible`; also re-check `test_plan_rebalance_postconditions_min_and_max_given` and `test_plan_rebalance_deterministic` (red without borrowing, green with it in the experiment).
  - test_rebalance_due.py: `test_default_flag_values` (823, `start_offset == 1` → 0), `test_e2e_range_invalid_forms_each_get_a_distinct_message` (1736; `0-30` is now valid and the LO failure mode no longer exists — reduce the test to the two reachable invalid forms, malformed (`abc`) and HI < LO (`30-8`), and assert their two messages are distinct, `len({msg_hi, msg_malformed}) == 2`; do not substitute a negative start, which lands on the malformed message), `test_e2e_full_apply_respects_bounds_preserves_ivl_never_moves_later`, `test_e2e_set_earlier_rescues_infeasible_run_and_extends_horizon`, `test_e2e_max_shift_limits_earlier_movement_and_reports_shortfall_not_failure` (~1280; "reported, not a failure (D6.1, settled)" → now exits non-zero and writes nothing; rename), `test_e2e_extended_horizon_message_fires_and_uses_offset_not_absolute_day`, `test_e2e_omitting_range_matches_the_pure_core_oracle_exactly`, `test_e2e_cap_unreachable_sliding_completes_and_reports_over_target_days`, `test_e2e_sliding_dry_run_produces_descending_shape_and_writes_nothing` (2094; its comment pins `_reached_exempt_tail` — new expectation: every day in [8, 16] or a clean non-zero exit, pick a fixture where it is feasible), and the stale exempt-tail comment in `test_render_histogram_day_not_in_short_days_never_marked_below_min` (655-666; strip the narration, assertion unchanged).
  - Planner-observed in the same experiment: test_due_stats.py, test_followup_fixes.py, test_min_separation_e2e.py, test_separation_repair_e2e.py stayed green — verify, do not assume.
- **Acceptance:** zero reds across the package; the exit report lists every rewritten test with old vs new assertion in one line each; no test removed without a named replacement; no remaining test asserts `start_offset == 1` as a default, a returned result with a day under `--min`, or `short_days != []` in flat mode.
- **Test oracle:** existing suite (rewritten to the new contracts; the shipped pre-fix behaviour is explicitly NOT the oracle).

## Phase 5: Verify

### 5.1: Full suite, lint, and the repro shape

- **File scope:** none (read-only verification).
- **Steps:** `uv run --group dev pytest` in `libs/python/anki-tools` (whole package, not only the rebalance files — planner baseline: two tests, `test_vocabulary_data.py::test_wheel_build_includes_tsv_data` and `test_card_layout.py::test_pre_4_1_template_fails_the_centre_assertion`, failed only in the planner's scratch copy for environment reasons and pass in the worktree); `uv run ruff format --check .` and `uv run ruff check .`; grep `anki_tools/` and `tests/` for `exempt`, `_reached_exempt_tail`, `D6.1`, `LO must be >= 1`, `default=1` on `--start-offset`, each paired with a positive-control grep that does hit; re-run the 1.1 repro case and record the per-day `after` counts in the exit report.
- **Acceptance:** all green; repro shape every day in [3, 4]; infeasible `--min` raises/exits non-zero with the collection unchanged.
- **Test oracle:** existing suite.

## Risks, open questions, decision points

**Risks**
- **R1 — no-range runs with `--min` become much stricter.** Without `--range` the window is `[start_day, latest card day]` (due_plan.py:831-833), often a year out. With the tail exemption gone and no `--set-earlier`, cards only move earlier, so every day out to the last card must already be reachable by cards originating at or after it. Many real no-range `--min` runs will now fail fast (precheck, after 2.2) — this is the user's stated requirement ("it should fail if the range can't be met"), not a regression, but the docs at Record must say so plainly and point at `--range` / `--set-earlier`.
- **R2 — greedy is not exact.** The min pass is a forward greedy sweep; with `max_shift` and separation it can fail on inputs a perfect assignment would satisfy. Requirement 5 allows "precheck feasible, planner raises"; the hard gate guarantees nothing short is ever returned. 2.2's agreement test measures it. See DP-1.
- **R3 — extended horizon.** With `--set-earlier` and no range, the reverse pass may extend `end_day`; the new days are in the window and need `--min` too. The precheck cannot see them (it uses the original latest day); the planner gate is the backstop.
- **R4 — backup before planner failure.** `main` takes the backup before `plan_rebalance` (rebalance_due.py:527-536). A `min unmet` raise therefore still leaves a backup file, but writes nothing to the collection — the same as today's mid-plan `InfeasibleRebalance`. Not changed.
- **R5 — sliding results shift.** Allowing the target-floor min pass to borrow later under `--set-earlier` changes sliding outputs for `--set-earlier` runs; tests pinning exact sliding numerals under `--set-earlier` will move (4.1 handles them).

**Decision points (human gate)**
- **DP-1 — exactness of the planner.** (A, recommended) Greedy min pass + necessary-condition precheck + hard gate: minimal, satisfies requirements 2 and 5 as worded, the acceptance shape passes. (B) Replace the min pass with an exact assignment (bipartite/flow over cards × days with min/max capacities): every precheck-feasible-in-principle input succeeds, but it is a rewrite of the planner core well beyond a bugfix and changes move selection everywhere.
- **DP-2 — dead flat-mode "below --min" histogram marker.** After 2.1 flat `short_days` is always empty, so `render_histogram`'s flat `"<- below --min"` marker (rebalance_due.py:206, 212-213) can never fire from `main`. (A, recommended for minimal scope) Leave the renderer and its direct tests (`test_render_histogram_marks_under_min_day_differently` 624, `test_sliding_short_day_marker_does_not_claim_below_min` in test_followup_fixes.py:102) unchanged — it renders what it is handed. (B) Delete the flat marker and rewrite those tests — cleaner, larger diff. 3.2 deletes only the unreachable `main()` label.
- **DP-3 — range-mode upper bound under `--set-earlier`.** (A, recommended, planned in 2.2 item 2) Make it a hard precheck violation, because the reverse pass cannot extend a `--range` window. (B) Leave the downgrade; the planner still raises `"range ceiling"`, just after the backup.
- **DP-4 — borrow order.** Planned: later sources first (existing behaviour), earlier surplus only as a fallback, nearest earlier day first. Alternative: whichever source minimizes displacement regardless of direction. Planned order keeps "earlier is the default direction" from the docs (README line 68).

**Assumptions not verified**
- That no other module besides `rebalance_due.py` and `due_stats.py` calls `plan_rebalance`, `apply_min_pass`, `parse_range`, or reads `short_days` (due_plan.py:5-6 claims `rebalance_due.py` is the only caller; the builder should grep `anki_tools/` to confirm before changing `apply_min_pass`'s signature).
- The 4.1 known-test list comes from a throwaway experiment, not the final implementation.

## Skill mapping

- **Build (one builder, one lane, serial):** subphases 1.1 → 2.1 → 2.2 → 3.1 → 3.2 → 4.1 → 5.1 run in one lane in the parent worktree `/home/icarus64/repos/daedalus-mono/.workflows/rebalance-min-tail` (branch `bug/rebalance-min-tail`). Serial because every subphase touches `due_plan.py`, `rebalance_due.py`, or the shared rebalance test files; no two subphases have disjoint scopes worth parallelizing. 1.1 and the new-contract parts of 2.1/2.2 → `contract-tester`; 2.1, 2.2, 3.1, 3.2 product code → `coder`; 4.1 test rewrites → `contract-tester` working from this plan's stated new contracts; 5.1 → the builder's own e2e verification. `init-workspace` for the uv env if needed.
- **Gates:** `review-plan` (this plan), `review-code` after build, `review-pr` against the branch diff vs `main` (no PR is opened on this repo — it lands by local merge; the gate still reviews the branch diff).
- **Record:** `documenter` → `document-local` updates `docs/libs/python/anki-tools/README.md`: the `--min` row (line 52), the `--max-shift` row's "reported, not errored" sentence (54), `--start-offset` default `1` → `0` and "today or overdue are never touched" → overdue only (60), `--range LO-HI` → `START-STOP` with 0 = today (61), the earlier-only paragraph's "default tomorrow" and "never placed on today" (68), card scope "not already due today" (75), the precheck section (80-87) for the new min-side window condition and the range-mode upper bound, `InfeasibleRebalance` reasons incl. `"min unmet"`/`"max unmet"` (257), `RebalanceResult.short_days` meaning (258), the `anki-due-stats` usage default (120-121). Grep the whole docs tree for `exempt`, `tail`, `tomorrow`, `start-offset` with a positive control. Plus a changelog entry. No attribution trailers of any kind in the record commit.
- **Landing:** local merge of `bug/rebalance-min-tail` into `main`, then push `main` — with the user's confirmation; no PR.
