# Anki Tools

A grab-bag of small standalone scripts for working with the Anki spaced-repetition app: building decks from delimited text files, inspecting a local Anki collection's deck/options-group structure, rebalancing review due dates across a deck and its subdecks (plus a read-only report on the same), and a one-off script for renaming MP3 filenames used in a Japanese-vocabulary deck build. The scripts are independent entry points, not a cohesive library.

**Path:** `libs/python/anki-tools`
**Workspace name:** `lib.python.anki-tools`

## Stack

- Python `>=3.11`, managed with [uv](https://docs.astral.sh/uv/) and built with hatchling (`pyproject.toml`, PEP 621 `[project]`). Dependencies resolve from the workspace-root `uv.lock`; there is no per-package lockfile.
- Runtime dependency: `anki`, unpinned — the resolved version comes from the root `uv.lock`. The tool is not tied to a specific Anki release; the suite is verified against whatever version the lock resolves.
- Dev dependency: `pytest`, declared in this package's `[dependency-groups] dev`. Declaring it there is load-bearing — without it the runner falls through to an ambient interpreter's pytest. Wired to `pnpm test` via `package.json`'s `"test": "py-test"`.

## Structure / entry points

- `anki_tools/__init__.py` — makes the package explicit. `import anki_tools` worked before this too (an implicit PEP 420 namespace package), so this is a packaging-stability fix, not a bugfix.
- `anki_tools/build_deck.py` — `build_deck()`/`build_decks()`, writes pipe-delimited deck text files from card data; has a CLI (`argparse`) entry point.
- `anki_tools/get_deck_info.py` — reads the local Anki collection (via the `anki` package's `Collection`), lists decks grouped by options group; has a `main()` CLI entry point.
- `anki_tools/mp3_filename_update.py` — one-off script hardcoded to a specific user's Anki media directory and a `created-decks/jlptsensei/...` folder structure; not general-purpose.
- `anki_tools/due_plan.py` — pure due-date rebalancing algorithm and feasibility analysis, zero Anki imports, fully unit-testable. See below.
- `anki_tools/rebalance_due.py` — CLI that resolves a deck against a real Anki collection and applies `due_plan`'s result. See below.
- `anki_tools/due_stats.py` — read-only CLI that reports `due_plan`'s feasibility/shape analysis for a deck without planning or writing anything. See below.
- `package.json` `bin` entries: `anki-build-deck`, `anki-get-deck-info`, `anki-mp3-filename-update`, `anki-rebalance-due`, `anki-due-stats`.
- `tests/test_due_plan.py`, `tests/test_rebalance_due.py`, `tests/test_due_stats.py` — pytest suites, 189 tests total.

## `anki-rebalance-due`

Rebalances the due dates of review cards in an Anki deck **and all of its subdecks** (Anki's `::` hierarchy) so that no scheduled day holds more than `--max` or fewer than `--min` cards.

```
anki-rebalance-due DECK [--min N] [--max N] [--max-shift N] [--set-earlier]
                        [--sliding] [--strict-sliding]
                        [--dry-run] [--yes]
                        [--start-offset N | --range LO-HI]
                        [--collection PATH] [--backup-dir PATH] [--no-backup]
```

| Flag | Default | Meaning |
|---|---|---|
| `DECK` (positional) | — required | Full deck name including `::` separators, e.g. `programming::coding`. Subdecks are always included. |
| `--min N` | none | Minimum cards per day. At least one of `--min`/`--max` is required. |
| `--max N` | none | Maximum cards per day — the hard cap, never exceeded regardless of mode. |
| `--max-shift N` | `14` | Furthest a card may move **earlier** than its original day, measured cumulatively from where it started. `--max-shift 0` disables all earlier movement; `--max-shift none` disables the cap entirely. Days that can't reach `--min` (or the sliding target) under the cap are reported, not errored. |
| `--set-earlier` | off | Enables a mirrored push-later rescue pass when `--max` can't be satisfied by moving cards earlier alone (see Invariant below). The only mode in which a card can move to a later date. |
| `--sliding` | off | Replace the flat `--min`/`--max` band with a per-day *target* that ramps linearly from `--max` at the window start down to `--min` at the horizon — the user's "slide" shape. `--max` stays the hard cap regardless. Requires both `--min` and `--max`. |
| `--strict-sliding` | off | With `--sliding`, fail (`InfeasibleRebalance`) instead of best-effort when `--max-shift` prevents the ramp from being fully reached. No effect without `--sliding`. |
| `--dry-run` | off | Prints the plan (day-by-day histogram) and writes nothing. A backup is still taken first (see Safety). |
| `--yes` / `-y` | off | Skips the interactive `y/N` confirmation before writing. |
| `--start-offset N` | `1` | Days after today where the rebalance window begins. Cards due today or overdue are never touched, in either mode. Mutually exclusive with `--range`. |
| `--range LO-HI` | none (full window) | Anki-style day-offset slice, e.g. `8-30` (or a bare `N` for `N-N`). Only cards due in `[today+LO, today+HI]` are in scope; moves are contained inside that window in both directions and the horizon never extends past `HI`. `--max-shift` is additionally clamped by `LO`. Mutually exclusive with `--start-offset`. Omit for the full window (unchanged default behavior). |
| `--collection PATH` | auto-detected | Override the Anki collection path (`~/.local/share/Anki2/User 1/collection.anki2` on POSIX, the `%AppData%` equivalent on Windows). |
| `--backup-dir PATH` | `<collection dir>/backups` | Where the pre-write `.colpkg` backup is written. |
| `--no-backup` | off | Skip the pre-write backup. |

### Core invariant

**A card's due date only ever moves earlier, never later — by default.** Max enforcement sweeps from the latest day backward, pushing overflow one day earlier at a time; min enforcement pulls cards forward from later days to fill underfull ones. When `--max` cannot be satisfied without moving something later, the default behavior is to **exit non-zero having written nothing** rather than violate the invariant. `--set-earlier` is the single, explicit escape hatch: after the earlier-only pass runs and comes up short, a mirrored pass may push excess cards **later** (extending the horizon past the last day if needed, unless `--range` pins it) so the run succeeds. Even with `--set-earlier`, no card is ever placed on today or earlier — the window start (`--start-offset`, default tomorrow, or `--range`'s `LO`) is untouchable in both directions.

### Move mechanics

- **One-day cascade.** Overflow from an over-max day always moves to exactly one day earlier (or, in the reverse pass, one day later) — never a search for the nearest day with free capacity. The receiving day's own excess is handled when the sweep reaches it.
- **Untouched-cards-first selection.** Within a day, cards that haven't moved yet this run are chosen before cards that have already moved, as the primary sort key. Only once untouched cards run out does an already-moved card get picked again (moves can legitimately cascade two or more days this way).
- **Tiebreakers by interval (`ivl`).** After the untouched-first key, the max passes prefer the largest-`ivl` card (a one-day nudge is proportionally smallest for a long-interval card); the min pass prefers the smallest-`ivl` card (cheapest to advance a longer distance). Final tiebreak is ascending card id, for determinism.
- **Card scope.** Only review-queue cards (`queue == 2 and type == 2`) that are not in a filtered deck and are not already due today or overdue (and, under `--range`, are inside the window). New, learning, relearning, suspended, buried, filtered-deck, and out-of-range cards are left untouched and counted in a skip report.
- **Interval preserved.** Moves go through `col.sched.set_due_date(cids, "N")` (non-bang form), which changes `due` and leaves `ivl` — and therefore the card's memory state — untouched. This tool moves *when* a card is seen next, not its scheduling strength.

### Feasibility precheck

Before anything else happens, a pure arithmetic check runs over the in-scope cards: the global average against `--max` and (if given) `--min`, plus a window (Hall-style) condition over every contiguous day range, which is what catches distributions that pass the average check but are still impossible to place (a dense early cluster, for example). **Both sides hard-fail with no escape flag** — this is deliberate, strict-by-default behavior, not a bug:

- `avg > max` (or a binding window inside it) → infeasible.
- `avg < min` (or a binding window) → infeasible. There is no `--skip-precheck`.

On failure the tool prints the arithmetic (total cards, horizon, avg/day, the violated bound, and the binding day range when relevant) and a suggested feasible `--min`/`--max`, then exits non-zero **before taking a backup or planning anything**. The three ways out are: lower `--min`, omit `--min` entirely (a max-only run skips the lower check), or narrow the window with `--range` to a denser slice.

In `--sliding` mode the precheck's hard gate is always against the flat `--max`/`--min`, never the ramp `T(d)` — a deck can be "shape-unreachable" (see below) while still being perfectly feasible. Reachability of the sliding shape itself is reported, never a reason to hard-fail, unless `--strict-sliding` is given.

### Sliding mode (`--sliding`)

Instead of a flat `[--min, --max]` band, the per-day target ramps linearly from `--max` at the window start down to `--min` at the horizon. `--max` remains the **hard cap** throughout — sliding never allows a day to exceed it — the ramp is a **soft target**: the algorithm first guarantees the hard cap exactly as in flat mode, then shapes downward toward the ramp as far as `--max-shift` allows.

Days that cannot be brought down to the ramp under the shift cap are left where they legally can be (still at or under `--max`) and reported as **over-target days**, plus the minimum `--max-shift` that *would* reach the full shape — this is `anki-due-stats`' best-effort default (DP-F). Pass `--strict-sliding` to turn that into a hard failure instead.

**On a back-loaded deck, the far end of the window may stay above the ramp under the default 14-day `--max-shift`** — moving a card scheduled eight months out down to a day-10 target is outside that budget. `anki-due-stats --sliding` reports the actual minimum `--max-shift` that would close the gap, so raising the cap (at the cost of moving mature cards further) is a deliberate choice rather than a discovery.

### Safety

The order is fixed and load-bearing: **open collection → collect in-scope cards → feasibility precheck → (pass) backup → plan → confirm → apply**. A failed precheck writes nothing and creates **no backup** — there is nothing to roll back, since nothing was touched. Once the precheck passes, a `.colpkg` backup is taken **on every run, including `--dry-run`** (unless `--no-backup`), before planning starts — so an `InfeasibleRebalance` raised later by planning itself still leaves a backup behind. After backup: `plan_rebalance` runs, the day-by-day histogram prints, and the run pauses for a `y/N` confirmation (unless `--yes` or `--dry-run`).

### Examples

Sliding dry-run, ramping from 16 cards/day near today down to 8 cards/day at the horizon:

```
anki-rebalance-due programming::coding --min 8 --max 16 --sliding --dry-run
```

Rebalance only the offset-8-to-30 slice of the deck (leaving everything else untouched):

```
anki-rebalance-due programming::coding --min 8 --max 16 --range 8-30
```

## `anki-due-stats`

Read-only feasibility/shape report — no planning, no writes, no backup, no prompt. Exits `0` whether the deck is feasible or not; it is a report, not a gate.

```
anki-due-stats DECK [--min N] [--max N] [--sliding]
                     [--start-offset N | --range LO-HI]
                     [--collection PATH]
```

Prints:
- totals, horizon, and average cards/day over the window (or the `--range` slice)
- the feasible flat `--min`/`--max` range for that window
- when `--min`/`--max` are given, whether that pair is feasible, with the binding arithmetic when not
- the sliding-shape profile: whether the ramp is reachable at the default `--max-shift` (14), the worst-window gap when it isn't, and **the minimum `--max-shift` that would make it reachable** — the same cap-aware reachability check `--sliding`/`--strict-sliding` rely on

Example — check whether `--min 8 --max 16 --sliding` would need a larger `--max-shift` before running it for real:

```
anki-due-stats programming::coding --min 8 --max 16 --sliding
```

## `due_plan.py` — the pure rebalancing core

`anki_tools/due_plan.py` has no Anki imports and does all of its work over plain `CardDue(card_id, day, ivl)` records and per-day target mappings, which is what makes the algorithm and its feasibility analysis unit-testable without a real collection. Its public surface:

- `validate_bounds(min_per_day, max_per_day)` — the "at least one of `--min`/`--max`" and `min <= max` checks.
- `plan_rebalance(cards, start_day, min_per_day, max_per_day, max_shift=14, set_earlier=False, sliding=False, strict_sliding=False, end_day=None) -> RebalanceResult` — the orchestration entry point: builds the day buckets (bounded by `end_day` in range mode), runs the max pass, the reverse (push-later) pass if needed and allowed, a shape pass toward the sliding ramp when `sliding=True`, then the min/floor pass, and validates post-conditions (no card below `start_day`, none above `end_day` in range mode, no unintended later moves, hard cap respected, multiset of card ids preserved).
- `InfeasibleRebalance` — raised when `--max` can't be satisfied without `--set-earlier` (or, in the pathological case, even with it), when `--range` containment can't absorb the excess, or (with `--strict-sliding`) when the ramp can't be fully reached; carries the offending days, their counts, and the reason (`"sink overflow"` / `"shift cap"` / a sliding-target reason).
- `RebalanceResult` — `moves` (`card_id -> new_day`, changed cards only), `before`/`after` per-day counts, `end_day` (possibly extended by the reverse pass, unless `--range` pins it), `sink_overflow`, `short_days` (days left under `--min`/the ramp floor because the shift cap blocked a fill — legal, reported rather than raised), `reverse_pass_used`, and `over_target_days` (days left above the sliding ramp `T(d)` — `[]` in flat mode).
- `check_feasibility(cards, start_day, end_day, min_per_day, max_per_day, max_shift, sliding=False, set_earlier=False) -> FeasibilityReport` — the precheck: always runs the hard flat-bound + window (Hall) check (`check_hard_feasibility`), and in sliding mode also runs the informational shape-reachability check (`analyze_shape`). Only the hard leg can make `feasible` false; the shape leg only ever populates `shape_reachable` / `predicted_over_target_days` / `min_feasible_max_shift` for reporting.
- `build_target_line(start_day, end_day, min_per_day, max_per_day) -> dict[int, int]` — the sliding ramp `T(d)`, linear from `max_per_day` at `start_day` to `min_per_day` at `end_day`.

`anki_tools/rebalance_due.py` is the only caller for planning: it resolves the deck (`resolve_deck_ids` — via `col.decks.id_for_name` + `col.decks.deck_and_child_ids`, so subdecks are always included), extracts in-scope cards (`collect_cards`, range-aware), runs `check_feasibility` before touching the collection, takes the backup, calls `plan_rebalance`, renders the histogram, and applies the result (`apply_moves`, one `set_due_date` call per distinct target day) after confirmation. `anki_tools/due_stats.py` calls the same `check_feasibility`/`build_target_line`/`analyze_shape` functions read-only, never `plan_rebalance`.

## Usage

- `package.json` scripts (`build`, `lint`, `dev`, `test`) shell out to `libs/bash/build-tools`'s `py-build`/`py-lint`/`py-dev`/`py-test` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- Run via `pnpm --filter lib.python.anki-tools <script>` or the `bin` commands (`anki-build-deck`, `anki-get-deck-info`, `anki-mp3-filename-update`, `anki-rebalance-due`, `anki-due-stats`) once installed.

## Testing

`tests/test_due_plan.py`, `tests/test_rebalance_due.py`, and `tests/test_due_stats.py` — 189 tests total (pytest, run via `uv run --group dev pytest` inside this package, or `pnpm --filter lib.python.anki-tools test` from the repo root). The `due_plan` suite is table-driven, hand-built distributions asserting on move counts and card *identity* (not just final counts) for the one-day-cascade and untouched-first-selection rules, plus the feasibility precheck, the sliding target line, and the cap-aware reachability bisection. The `rebalance_due` suite drives a synthetic temporary Anki collection end to end — subdeck inclusion, skip-report correctness, real (non-dry-run) apply, `--dry-run` no-op, `--set-earlier` rescue, `--max-shift` capping, `--range` containment, `--sliding`/`--strict-sliding`, and default-mode infeasibility (both the precheck failure and a mid-plan `InfeasibleRebalance`) leaving the real collection byte-for-byte unchanged, with backup presence asserted differently for each failure mode. `test_due_stats.py` covers the read-only report end to end, including that it never creates a backup or changes the collection's mtime. No test opens the user's real collection.

## Notes

- **In the pnpm workspace** (matched by the `libs/*/*` glob) and driven by root turbo.
- Two independent lint toolchains apply to this package: `pnpm lint` runs `ruff check .` (unpinned, currently 0.16.2, default rule set); a separate `PostToolUse` editor hook enforces `black` formatting + `flake8` (88-column). New code is clean under both; the pre-existing 11 findings in `build_deck.py`/`get_deck_info.py`/`mp3_filename_update.py` are untouched legacy debt, out of scope for this change.
- `libs/python/anki-tools/BUILD` is a 0-byte vestigial Bazel file — legacy and unused.
- The pre-existing `args = parser.parse_known_args()` bug in `build_deck.py` (a tuple used as if it were the namespace) is a known, separate issue — not touched by the rebalance feature.
