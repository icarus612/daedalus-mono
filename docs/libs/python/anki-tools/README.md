# Anki Tools

A grab-bag of small standalone scripts for working with the Anki spaced-repetition app: building decks from delimited text files, inspecting a local Anki collection's deck/options-group structure, rebalancing review due dates across a deck and its subdecks, and a one-off script for renaming MP3 filenames used in a Japanese-vocabulary deck build. The scripts are independent entry points, not a cohesive library.

**Path:** `libs/python/anki-tools`
**Workspace name:** `lib.python.anki-tools`

## Stack

- Python `^3.11` via Poetry (`pyproject.toml` + `poetry.lock`). The repo's effective Poetry is the one installed **inside the package's own `.venv`** by `libs/bash/build-tools`'s `py-install` (currently `2.4.1`), not whatever Poetry is on `PATH`.
- Runtime dependency: `anki 24.06.3`, pinned exact (`poetry.lock` normalizes the pin to `24.6.3` per PEP 440 — both spellings are correct; `anki.buildinfo.version` remains the string `'24.06.3'`).
- Dev dependency: `pytest` — this package is the **first Python package in the monorepo with a test suite**, wired to `pnpm test` via `package.json`'s `"test": "poetry run pytest"`.

## Structure / entry points

- `anki_tools/__init__.py` — makes the package explicit. `import anki_tools` worked before this too (an implicit PEP 420 namespace package), so this is a packaging-stability fix, not a bugfix.
- `anki_tools/build_deck.py` — `build_deck()`/`build_decks()`, writes pipe-delimited deck text files from card data; has a CLI (`argparse`) entry point.
- `anki_tools/get_deck_info.py` — reads the local Anki collection (via the `anki` package's `Collection`), lists decks grouped by options group; has a `main()` CLI entry point.
- `anki_tools/mp3_filename_update.py` — one-off script hardcoded to a specific user's Anki media directory and a `created-decks/jlptsensei/...` folder structure; not general-purpose.
- `anki_tools/due_plan.py` — pure due-date rebalancing algorithm, zero Anki imports, fully unit-testable. See below.
- `anki_tools/rebalance_due.py` — CLI that resolves a deck against a real Anki collection and applies `due_plan`'s result. See below.
- `package.json` `bin` entries: `anki-build-deck`, `anki-get-deck-info`, `anki-mp3-filename-update`, `anki-rebalance-due`.
- `tests/test_due_plan.py`, `tests/test_rebalance_due.py` — pytest suites, 111 tests total.

## `anki-rebalance-due`

Rebalances the due dates of review cards in an Anki deck **and all of its subdecks** (Anki's `::` hierarchy) so that no scheduled day holds more than `--max` or fewer than `--min` cards.

```
anki-rebalance-due DECK [--min N] [--max N] [--max-shift N] [--set-earlier]
                        [--dry-run] [--yes] [--start-offset N]
                        [--collection PATH] [--backup-dir PATH] [--no-backup]
```

| Flag | Default | Meaning |
|---|---|---|
| `DECK` (positional) | — required | Full deck name including `::` separators, e.g. `programming::coding`. Subdecks are always included. |
| `--min N` | none | Minimum cards per day. At least one of `--min`/`--max` is required. |
| `--max N` | none | Maximum cards per day. |
| `--max-shift N` | `14` | Furthest a card may move **earlier** than its original day, measured cumulatively from where it started. `--max-shift 0` disables all earlier movement; `--max-shift none` disables the cap entirely. Days that can't reach `--min` under the cap are reported, not errored. |
| `--set-earlier` | off | Enables a mirrored push-later rescue pass when `--max` can't be satisfied by moving cards earlier alone (see Invariant below). The only mode in which a card can move to a later date. |
| `--dry-run` | off | Prints the plan (day-by-day histogram) and writes nothing. |
| `--yes` / `-y` | off | Skips the interactive `y/N` confirmation before writing. |
| `--start-offset N` | `1` | Days after today where the rebalance window begins. Cards due today or overdue are never touched, in either mode. |
| `--collection PATH` | auto-detected | Override the Anki collection path (`~/.local/share/Anki2/User 1/collection.anki2` on POSIX, the `%AppData%` equivalent on Windows). |
| `--backup-dir PATH` | `<collection dir>/backups` | Where the pre-write `.colpkg` backup is written. |
| `--no-backup` | off | Skip the pre-write backup. |

### Core invariant

**A card's due date only ever moves earlier, never later — by default.** Max enforcement sweeps from the latest day backward, pushing overflow one day earlier at a time; min enforcement pulls cards forward from later days to fill underfull ones. When `--max` cannot be satisfied without moving something later, the default behavior is to **exit non-zero having written nothing** rather than violate the invariant. `--set-earlier` is the single, explicit escape hatch: after the earlier-only pass runs and comes up short, a mirrored pass may push excess cards **later** (extending the horizon past the last day if needed) so the run succeeds. Even with `--set-earlier`, no card is ever placed on today or earlier — the window start (`--start-offset`, default tomorrow) is untouchable in both directions.

### Move mechanics

- **One-day cascade.** Overflow from an over-max day always moves to exactly one day earlier (or, in the reverse pass, one day later) — never a search for the nearest day with free capacity. The receiving day's own excess is handled when the sweep reaches it.
- **Untouched-cards-first selection.** Within a day, cards that haven't moved yet this run are chosen before cards that have already moved, as the primary sort key. Only once untouched cards run out does an already-moved card get picked again (moves can legitimately cascade two or more days this way).
- **Tiebreakers by interval (`ivl`).** After the untouched-first key, the max passes prefer the largest-`ivl` card (a one-day nudge is proportionally smallest for a long-interval card); the min pass prefers the smallest-`ivl` card (cheapest to advance a longer distance). Final tiebreak is ascending card id, for determinism.
- **Card scope.** Only review-queue cards (`queue == 2 and type == 2`) that are not in a filtered deck and are not already due today or overdue. New, learning, relearning, suspended, buried, and filtered-deck cards are left untouched and counted in a skip report.
- **Interval preserved.** Moves go through `col.sched.set_due_date(cids, "N")` (non-bang form), which changes `due` and leaves `ivl` — and therefore the card's memory state — untouched. This tool moves *when* a card is seen next, not its scheduling strength.

### Safety

Before writing: `plan_rebalance` runs to completion first (so an infeasible plan aborts with nothing touched), then a `.colpkg` backup is taken (unless `--no-backup`), then a day-by-day histogram is printed and the run pauses for a `y/N` confirmation (unless `--yes` or `--dry-run`). `--dry-run` prints the same histogram and takes no backup.

### Example

```
anki-rebalance-due programming::coding --min 8 --max 16 --dry-run
```

## `due_plan.py` — the pure rebalancing core

`anki_tools/due_plan.py` has no Anki imports and does all of its work over plain `CardDue(card_id, day, ivl)` records and day-number buckets, which is what makes the algorithm unit-testable without a real collection. Its public surface:

- `validate_bounds(min_per_day, max_per_day)` — the "at least one of `--min`/`--max`" and `min <= max` checks.
- `plan_rebalance(cards, start_day, min_per_day, max_per_day, max_shift=14, set_earlier=False) -> RebalanceResult` — the orchestration entry point: builds the day buckets, runs the max pass, the reverse (push-later) pass if needed and allowed, then the min pass, and validates post-conditions (no card below `start_day`, no unintended later moves, all days within bounds where required, multiset of card ids preserved).
- `InfeasibleRebalance` — raised when `--max` can't be satisfied without `--set-earlier` (or, in the pathological case, even with it); carries the offending days, their counts, and the reason.
- `RebalanceResult` — `moves` (`card_id -> new_day`, changed cards only), `before`/`after` per-day counts, `end_day` (possibly extended by the reverse pass), `sink_overflow`, `short_days` (days left under `--min` because the shift cap blocked a fill — legal, reported rather than raised), and `reverse_pass_used`.

`anki_tools/rebalance_due.py` is the only caller: it resolves the deck (`resolve_deck_ids` — via `col.decks.id_for_name` + `col.decks.deck_and_child_ids`, so subdecks are always included), extracts in-scope cards (`collect_cards`), calls `plan_rebalance`, renders the histogram, and applies the result (`apply_moves`, one `set_due_date` call per distinct target day) after backup and confirmation.

## Usage

- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`. `test` runs `poetry run pytest` directly.
- Run via `pnpm --filter lib.python.anki-tools <script>` or the `bin` commands (`anki-build-deck`, `anki-get-deck-info`, `anki-mp3-filename-update`, `anki-rebalance-due`) once installed.

## Testing

`tests/test_due_plan.py` and `tests/test_rebalance_due.py` — 111 tests total (pytest, run via `.venv/bin/poetry run pytest` inside this package, or `pnpm --filter lib.python.anki-tools test` from the repo root). The `due_plan` suite is table-driven, hand-built distributions asserting on move counts and card *identity* (not just final counts) for the one-day-cascade and untouched-first-selection rules. The `rebalance_due` suite drives a synthetic temporary Anki collection end to end — subdeck inclusion, skip-report correctness, real (non-dry-run) apply, `--dry-run` no-op, `--set-earlier` rescue, `--max-shift` capping, and default-mode infeasibility leaving the real collection byte-for-byte unchanged. No test opens the user's real collection.

## Notes

- **In the pnpm workspace** (matched by the `libs/*/*` glob) and driven by root turbo.
- Two independent lint toolchains apply to this package: `pnpm lint` runs `ruff check .` (unpinned, currently 0.16.2, default rule set); a separate `PostToolUse` editor hook enforces `black` formatting + `flake8` (88-column). New code in `due_plan.py`/`rebalance_due.py` is clean under both; the pre-existing 11 findings in `build_deck.py`/`get_deck_info.py`/`mp3_filename_update.py` are untouched legacy debt, out of scope for this change.
- `libs/python/anki-tools/BUILD` is a 0-byte vestigial Bazel file — legacy and unused.
- The pre-existing `args = parser.parse_known_args()` bug in `build_deck.py` (a tuple used as if it were the namespace) is a known, separate issue — not touched by the rebalance feature.
