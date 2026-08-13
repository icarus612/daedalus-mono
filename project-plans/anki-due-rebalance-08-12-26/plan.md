# anki-due-rebalance-08-12-26

Rebalance Anki review due dates across a deck and its subdecks so no scheduled day exceeds `--max` or falls below `--min`.

## Phase syllabus

- [ ] Phase 1: Package plumbing & dependency declaration
  - [x] 1.1: Make `anki_tools` an importable package, declare the `anki` runtime dep and the pytest dev dep, wire the `test` script and the new `bin` entry
- [ ] Phase 2: Pure rebalancing core (`due_plan.py`)
  - [x] 2.1: Data shapes, bound validation, run state, bucket construction, selection orders (after: 1.1)
  - [x] 2.2: Max pass — descending sweep, one-day cascade earlier, shift cap (after: 2.1)
  - [x] 2.3: Reverse max pass — ascending sweep, one-day cascade later, horizon extension (after: 2.2)
  - [x] 2.4: Min pass — ascending sweep, deficits filled from later days, shift cap (after: 2.1)
  - [x] 2.5: `plan_rebalance` orchestration, infeasibility handling, post-conditions (after: 2.2, 2.3, 2.4)
- [ ] Phase 3: Anki collection adapter & CLI (`rebalance_due.py`)
  - [x] 3.1: Collection open/close, deck+subdeck resolution, in-scope card extraction (after: 1.1, 2.1)
  - [x] 3.2: Apply moves via `set_due_date`, backup, dry-run histogram rendering (after: 2.5, 3.1)
  - [x] 3.3: argparse CLI wiring and argument validation (after: 3.2)
- [ ] Phase 4: Verification
  - [x] 4.1: End-to-end integration coverage against a synthetic temporary collection (after: 3.3)
  - [x] 4.2: No new lint findings, suite green, manual dry-run against the real collection (after: 4.1)
- [ ] Phase 5: Scope smart-lint to the triggering file
  - [ ] 5.1: Scope hook-mode linting to the triggering file
  - [ ] 5.2: Verify hook-mode scoping and CLI-mode preservation (after: 5.1)

Single lane. **Reason:** the whole feature is two new source files plus one shared manifest touchpoint inside one package (`libs/python/anki-tools/`), and both source files are written against a single data contract defined in 2.1. Splitting the pure core from the adapter would create a shared-types touchpoint larger than either lane, so lanes are not manufactured here.

*Recorded alternative (plan-review N8):* once 2.1 lands, 3.1 is genuinely independent of 2.2–2.4, and a two-lane split (lane 1: `due_plan.py`, 2.2–2.4; lane 2: `rebalance_due.py`, 3.1) with a serialized join at 3.2 would have disjoint file scopes. It was considered and rejected on coordination cost at this size, not overlooked. Revisit only if the feature grows.

**Note on `after:` edges.** The plan executes serially in syllabus order, so the edges above are documentation rather than a live schedule. They are declared accurately anyway (3.1 consumes the `CardDue` dataclass from 2.1) so that a future dispatcher cannot reorder the work into a break.

## Goal & scope

### Goal

Add a Python script to `libs/python/anki-tools` that takes a deck name, gathers the scheduled review cards of that deck **and all of its subdecks** (Anki's `::` hierarchy; the user's current target is `programming::coding`), and rewrites their due dates so the per-day card count falls inside `[--min, --max]`.

Verbatim rules from the request, which are the acceptance contract:

1. There must be a `--max` and a `--min` argument. Neither is individually required, but **at least one must be present** (error otherwise).
2. The modifier must ensure no day has more than the max or fewer than the min.
3. Max enforcement **starts from the end** (the latest due day) and **pushes cards to earlier dates**.
4. Min enforcement **takes cards from later dates** to fill an underfull day.
5. First real invocation: `--min 8 --max 16` on `programming::coding`.

Rules 3 and 4 together yield the plan's central invariant:

> **A card's due date only ever moves EARLIER, never later.**

**That invariant is absolute in the default mode and is the reason the run can fail.** When `--max` cannot be satisfied without moving something later, the default behaviour is to **exit non-zero having written nothing** (settled D3) — the plan refuses rather than silently violating it.

The single, explicit escape hatch is the settled `--set-earlier` flag (default `false`). With it on, and only after the earlier-only pass has already run and come up short, a mirrored pass may move cards **later** — the user's *"reverse the process"*. Even then, **no card is ever placed on today or earlier** (settled D2); the window start is untouchable in both directions.

### In scope

- New pure module `libs/python/anki-tools/anki_tools/due_plan.py` — the rebalancing algorithm, zero Anki imports, fully unit-testable.
- New CLI script `libs/python/anki-tools/anki_tools/rebalance_due.py` — Anki collection I/O, applies the plan.
- `libs/python/anki-tools/anki_tools/__init__.py` (currently missing — see Risks).
- `libs/python/anki-tools/pyproject.toml`: declare the `anki` runtime dependency (today it is an undeclared import) and a pytest dev dependency.
- `libs/python/anki-tools/package.json`: add the `bin` entry and a `test` script.
- New `libs/python/anki-tools/tests/` — the first Python tests in this monorepo.
- **`libs/prompting/claude/hooks/smart-lint.sh`** (Phase 5) — a user-ordered scope addition, unrelated to the Anki feature, riding this branch because PR #12 was already open. Its file scope is disjoint from everything above, so it cannot interfere. Phase 5 also performs an out-of-repo install to `~/.claude/hooks/smart-lint.sh`, which is an install action rather than a product change and never appears in the branch diff.

### Out of scope

- **Documentation.** No `README.md` or `/docs` edits in the build phases; the run's `document-local` stage owns that. `libs/python/anki-tools/README.md` is currently boilerplate profile text with nothing about the package (verified by reading it), and a repo-wide docs migration to symlinks is already in flight in the main working tree (`git status` shows type-changes on many `README.md` files). Do not touch it here.
- Touching any other package under `libs/python/*`, or `libs/bash/build-tools`. The `py-test` alternative that would have widened this was considered and rejected (D8).
- Fixing the pre-existing latent bug in `anki_tools/build_deck.py` (`args = parser.parse_known_args()` returns a tuple but is then used as `args.cardsfile`). Out of scope; note it for a separate change.
- Rescheduling new cards, learning cards, suspended cards, buried cards, or cards inside filtered decks (see decision D1).
- Moving any card to a **later** date **by default**. This is in scope only behind the settled `--set-earlier` flag, which is off unless asked for (D3, subphase 2.3).
- Moving any card onto today or an earlier day, in any mode whatsoever (D2).

## Stack & MAJOR versions

Every value below was read from a manifest, a lockfile, or the installed package — none from memory.

| Thing | Version | Verified from |
|---|---|---|
| Python | 3.11.7 (`python3` on PATH is a pyenv shim) | `python3 --version`; `libs/python/anki-tools/pyproject.toml` declares `python = "^3.11"` |
| `anki` Python library | **24.06.3** | `pip3 show anki`; `anki.buildinfo.version`. Installed at `/home/icarus64/.pyenv/versions/3.11.7/lib/python3.11/site-packages/anki`. `anki.__file__` is `None` (namespace-style package) — use `anki.buildinfo.version` to check it, not `__file__`. |
| Poetry | 1.8.2 | `poetry --version` |
| `libs/python/anki-tools` declared deps | **none** beyond `python = "^3.11"` | `libs/python/anki-tools/pyproject.toml`; `poetry.lock` has `package = []` |
| pytest | 7.4.3 (global interpreter only, not in the package `.venv`) | `python3 -m pytest --version` |
| pnpm / package manager | pnpm 9.1.0 | root `package.json` `"packageManager": "pnpm@9.1.0"` |
| Turborepo | `latest` | root `package.json` devDependencies; `turbo.json` defines `build`/`test`/`lint`/`dev` tasks |
| Python linter (`py-lint`) | **`ruff`, unpinned → currently 0.16.2, default rule set = 413 rules enabled** | `libs/bash/build-tools/py-scripts/py-lint` does `pip install -q ruff` (no version) then `ruff check .`. Verified by the plan gate with `ruff check --show-settings`: no config file exists anywhere in the repo (no `ruff.toml`, `.ruff.toml`, `setup.cfg`, `.flake8`, `[tool.ruff]`, `[tool.black]`, `[tool.mypy]`, no `~/.config/ruff/`, no `RUFF_*` env). "Default" here means 413 rules, **not** the E4/E7/E9/F subset — see R7. **Point-in-time caveat:** the *main working tree*'s copy of `libs/python/anki-tools/pyproject.toml` has since acquired an uncommitted, hook-added `[tool.black] force-exclude` block. HEAD and this run's worktree are both still clean of it, so nothing here breaks — but treat "no config anywhere" as a statement about HEAD, and re-check before relying on it. |
| Python linter (`PostToolUse` hook) | **`black` + `flake8`**, a *different* toolchain from `py-lint` | Observed live: `~/.claude/hooks/smart-lint.sh` reformats with black and reports `Flake8 found issues`, including `E501 line too long (> 88 characters)`. New code must satisfy **both** gates: black formatting + flake8 (88-col), and ruff 0.16.2 defaults. |
| Anki collection under test | `~/.local/share/Anki2/User 1/collection.anki2`, single profile `User 1` | `ls -l`. **Point-in-time only:** the file was 34,742,272 bytes with a `-wal` sidecar during planning, and 33,783,808 bytes with no `-wal` by the time of plan review — Anki was opened and closed in between. Treat only the durable facts as load-bearing: one profile, a large live collection, and *close Anki before running*. Never cite the byte count as fixed. |

### Empirically verified Anki 24.06.3 API behaviour

These were confirmed by running a probe against a freshly created throwaway collection (`Collection(<tmp>/probe.anki2)`), not assumed. The plan depends on all five:

1. **`col.decks.deck_and_child_ids(deck_id) -> list[DeckId]`** returns the deck plus every descendant. Probe: `programming::coding` returned `[<coding>, <coding::python>]`. Source: `anki/decks.py:476`.
2. **`col.find_cards('deck:"programming::coding"')` already includes subdecks** — the probe returned all 4 cards across parent and child, whereas `did:<id>` returned only the 2 cards in the deck itself. Either route works; 3.1 specifies the explicit `deck_and_child_ids` route because it is exactly testable and avoids search-string escaping.
3. **`col.sched.set_due_date(card_ids, "N")` sets `due = today + N` and LEAVES `ivl` UNCHANGED** for a review card. Probe: a card with `ivl=30`, `due=today+10` became `due=today+5`, `ivl=30`. With the bang form `"5!"` the same card became `due=today+5`, `ivl=5`. A **new** card given `"5"` was converted to `type=2, queue=2, due=today+5, ivl=5`. Signature at `anki/scheduler/base.py:203`; docstring: *"Set cards to be due in `days`, turning them into review cards if necessary. `days` can be of the form '5' or '5-7'."* This is why 3.2 uses the **non-bang** form.
4. **`col.sched.today`** is the integer day number the review-queue `due` column is expressed in (`anki/scheduler/base.py:53`). `anki/cards.py` header comment: *"Due is used differently for different queues. - new queue: position - rev queue: integer day - lrn queue: integer timestamp"*, and *"Type: 0=new, 1=learning, 2=due; Queue: same as above, and: -1=suspended, -2=user buried, -3=sched buried"*.
5. **`col.create_backup(*, backup_folder: str, force: bool, wait_for_completion: bool) -> bool`** exists (`anki/collection.py:323`) — keyword-only, *"Create a backup if enough time has elapsed, and rotate old backups. If `force` is true, the user's configured backup interval is ignored. Returns true if backup created. This may be false in the force=True case, if no changes have been made to the collection."* The profile's real backup folder is `~/.local/share/Anki2/User 1/backups` (verified: contains `backup-2026-08-12-09.19.56.colpkg` and older).

## Conventions to enforce

Hard constraints, each traced to observed repo evidence.

- **Location.** New code goes in `libs/python/anki-tools/anki_tools/`. There is no precedent anywhere in the repo for importing across `libs/python/*` packages via the workspace/Poetry graph — the only cross-directory Python import in the whole repo is a `sys.path.insert` hack in the Flask apps reaching `libs/python/flask_utils`. **Do not import from a sibling `libs/python/*` package.**
- **CLI style: `argparse` only.** No `click`, no `typer` — neither appears anywhere in the repo. Follow the `main()` + `if __name__ == "__main__": main()` shape of `anki_tools/get_deck_info.py`.
- **Indentation: 4 spaces.** Indentation is per-file chaotic across the repo (tabs in `web-crawlers`, 2 spaces in `mp3_filename_update.py`, mixed in `build_deck.py`). Match `anki_tools/get_deck_info.py`, the newest and cleanest file in this package and the only one with a `main()` entry point. `.vscode/settings.json` in this package sets `"python.formatting.provider": "autopep8"`, which is 4-space too.
- **Cite by symbol, not only by line.** All `get_deck_info.py` line numbers below are exact against `git show HEAD:…`, but the `PostToolUse` formatter reflows that file on almost every write — at plan-review time the same symbols had already shifted to `:6-14`, `:42-43`, `:62`, `:63-65`. **Locate by symbol name; treat the line number as a hint.**
- **Collection path resolution.** Reuse the exact platform-switch shape of `get_anki_collection_path()` (`anki_tools/get_deck_info.py:5-11` at HEAD): Windows `~\AppData\Roaming\Anki2\User 1\collection.anki2`, POSIX `~/.local/share/Anki2/User 1/collection.anki2`, else `raise OSError`. Verified correct against this machine.
- **Anki-is-running failure mode — preserve the message, NOT the broad `except`.** `get_deck_info.py`'s `main()` (`:59-61` at HEAD) does `except Exception` and prints *"Make sure Anki is not running when you execute this script."* Keep the user-facing guidance; **do not copy the blind except**, which is precisely why that file carries `BLE001` today. Instead catch the real types — verified present in `anki/errors.py`:
  - `anki.errors.DBError` (`errors.py:82`) for the locked/contended collection, which is what a running Anki produces → print the "Anki is not running" hint.
  - `anki.errors.AnkiException` (`errors.py:13`, the root of `BackendError` and everything else Anki raises) as the general Anki-failure fallback.

  This satisfies `BLE001` by construction — **no `# noqa` anywhere in the new files.** A `noqa` would be suppressing a rule the new code can simply comply with.
- **Always `col.close()`, including on the error path — via `try/finally`. This is the THIRD deliberate divergence** from the neighbour being copied. Verified at HEAD: `get_deck_info.py`'s `col.close()` (`:58`) sits *inside* the `try`, with the `except` at `:59-61`, so the cited example does **not** close on the error path. Copying its shape verbatim would fail 3.1's own acceptance criterion. Wrap the collection work in `try/finally` instead.
- **`bin` registration and the shebang.** Every runnable script in this package is registered in `libs/python/anki-tools/package.json` under `"bin"` (`anki-build-deck`, `anki-get-deck-info`, `anki-mp3-filename-update`). The new script gets `"anki-rebalance-due": "anki_tools/rebalance_due.py"` and must be mode 755 like the other three. **`rebalance_due.py` MUST begin with `#!/usr/bin/env python3`.** The three existing scripts are executable *without* a shebang, which is exactly what earns them `EXE002` — so here the new file deliberately **diverges from the neighbouring pattern**, because the pattern is the lint debt. Do not add shebangs to the existing three; that is the out-of-scope cleanup.
- **Lint gate — two independent toolchains, both must be satisfied.** New code must be clean under *both*:
  1. `py-lint` → `ruff check .` (unpinned ruff, currently 0.16.2, 413 default rules).
  2. The `PostToolUse` hook → `black` formatting + `flake8`, including **E501 at 88 columns**.

  Practically: format new files with **black defaults (88 cols, 4-space indent)**, which satisfies both gates at once and matches the `autopep8`/4-space convention already in `.vscode/settings.json`.

  **The gate is differential, not absolute** (see 1.1 and 4.2): *no NEW findings versus a captured baseline*. Pre-existing lint debt in this monorepo is explicitly out of scope for this run, per the user's decision at the plan gate. Do not add a ruff or flake8 config file; do not "fix" neighbouring files to make a total count go to zero.
- **No `# noqa`, no time estimates, no `TODO`s in final code**, per the repo's global instructions.

## Phased subphases

---

### Phase 1: Package plumbing & dependency declaration

#### 1.1: Make `anki_tools` an importable package, declare deps, wire scripts

**File scope**
- `libs/python/anki-tools/anki_tools/__init__.py` (new, empty or a one-line docstring)
- `libs/python/anki-tools/pyproject.toml` (edit)
- `libs/python/anki-tools/poetry.lock` (regenerated)
- `libs/python/anki-tools/package.json` (edit)
- `libs/python/anki-tools/tests/__init__.py` (new, empty) — only if needed for import resolution

**Why this is first and alone.** These are the shared touchpoints (manifest, lockfile, package.json). Everything else in the plan depends on them, and nothing else may edit them.

**Pattern to follow.** The existing `[tool.poetry.dependencies]` block in this same file; the existing `"bin"` map in `libs/python/anki-tools/package.json`.

**Work**

**Step 0 — capture the lint and scope baselines BEFORE touching anything.** This is the first action of the whole build, and every later acceptance criterion is measured against it. Write all three into the run dir (`<parent-worktree>/.artifacts/`), not the plans dir:
- `ruff-baseline.txt` — `ruff check --output-format=concise .` from `libs/python/anki-tools/`, exit code ignored. At HEAD this is **11 findings** (verified at plan review with ruff 0.16.2): `EXE002`×3, `I001`×3, `FURB122`, `F841` (`get_deck_info.py`, `deck_id`), `BLE001` (`get_deck_info.py`), `RUF010`, `F401` (`mp3_filename_update.py`).
- `flake8-baseline.txt` — the `PostToolUse` hook's flake8 findings for the same directory.
- `scope-baseline.txt` — `git -C <parent-worktree> status --porcelain`, capturing the files the formatter hook has *already* dirtied before any build work begins.
- `pnpm-lint-baseline.txt` — `pnpm lint` from the repo root, exit code ignored. **Expect it to be RED for this package already**: `py-lint` is `set -e` around a bare `ruff check .`, and the package has 11 pre-existing findings, so `turbo lint` fails here today. Without this capture a builder cannot tell pre-existing red from a regression it caused.
- `pnpm-test-baseline.txt` — `pnpm test` from the repo root, exit code ignored.

**Caveat on the `pnpm test` baseline.** Adding `"test": "poetry run pytest"` makes `anki-tools` the **first Python package in the monorepo with a `test` script** (verified: the only `test` scripts today are 6 Go and 5 JS packages). So `turbo test` gains a task that did not exist before, and the before/after comparison is **not** like-for-like for this package. Compare the *other* packages' results for regression; for `anki-tools` itself, "before" is simply absent.

Then:
- Create `anki_tools/__init__.py` (empty, or a one-line docstring). **Reason, corrected:** `import anki_tools` already succeeds today as a PEP 420 *namespace* package (`__file__ is None`, `__path__` is a `_NamespacePath`), because the editable install's `.pth` puts the package root on `sys.path`. So this is **not** fixing a current import failure — do not go hunting for one. It is making the packaging explicit and stable, so imports behave the same under pytest, `poetry run`, the hook's global interpreter, and a built wheel, and so `packages = [{include = "anki_tools"}]` in `pyproject.toml` is actually true.
- Add to `[tool.poetry.dependencies]`: `anki = "24.06.3"`. Pin the exact installed version (decision D9). **Expect the lock to normalize this to `24.6.3`** (PEP 440 strips the leading zero) — verified. That is correct and must not be "fixed"; `anki.buildinfo.version` remains the string `'24.06.3'`, so the two differing spellings are both right.
- Add a dev-dependency group with `pytest` (see decision D8).
- Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]` to `pyproject.toml` — the only pytest configuration in the repo, and it belongs here rather than in a new `pytest.ini`, because the repo has zero standalone tool-config files.
- `package.json`: add `"test": "poetry run pytest"` to `scripts`, and `"anki-rebalance-due": "anki_tools/rebalance_due.py"` to `"bin"`.
- Regenerate the lock with **`.venv/bin/poetry lock`** — see the toolchain note below.

**Which Poetry to use.** `libs/bash/build-tools/py-scripts/py-install` does `python3 -m venv .venv; source .venv/bin/activate; pip install poetry; poetry install`, so the repo's effective Poetry is the one **inside `.venv`** (currently **2.4.1** with poetry-core 2.4.0), *not* the 1.8.2 on `PATH`. Always invoke `.venv/bin/poetry` (or activate first). Do not use the PATH poetry for the lock.

**Acceptance criteria**
- `.venv/bin/poetry lock` then `.venv/bin/poetry install` succeed.
- `.venv/bin/python -c "import anki_tools; from anki.collection import Collection; import anki.buildinfo; print(anki.buildinfo.version)"` prints `24.06.3`. Today the `anki` half of that fails: `.venv/bin/python -c "import anki"` raises `ModuleNotFoundError` (verified at plan review), because the dependency is undeclared — the existing `get_deck_info.py` only runs by accident under the global pyenv interpreter.
- `.venv/bin/python -m pytest --version` succeeds.
- `poetry.lock` no longer has `package = []` and contains an `anki` entry at `24.6.3`.
- **Lint: no NEW findings.** `ruff check --output-format=concise .` diffed against `ruff-baseline.txt` adds nothing. The absolute count stays at the baseline's 11 — it does **not** go to zero, and driving it to zero is out of scope. Same rule for flake8.

**Test approach — oracle: `existing suite`** (there is none yet; this subphase's oracle is the commands above, run and pasted into the exit report). No behavioural code is added here.

**Note (not a blocker).** `poetry.lock`'s header says *"automatically @generated by Poetry 2.1.3"* with `lock-version = "2.1"`. That is consistent with the `.venv` Poetry 2.4.1 and is a non-issue; the plan gate ran the real operation on a throwaway copy of the manifests — adding `anki = "24.06.3"` and running `.venv/bin/poetry lock` **succeeds** ("Writing lock file", exit 0). Only the PATH-level Poetry 1.8.2 would have had a lock-format concern, and it is not the tool in play (it nonetheless accepts the existing lock: `poetry check --lock` → "All set!"). Do not stop the run over this.

---

### Phase 2: Pure rebalancing core (`due_plan.py`)

All of Phase 2 lives in one new file, `libs/python/anki-tools/anki_tools/due_plan.py`, and **imports nothing from `anki`**. That is the point: the algorithm is the risky part and it must be testable without a collection.

#### 2.1: Data shapes, bound validation, run state, bucket construction, selection orders

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py` (new)
- `libs/python/anki-tools/tests/test_due_plan.py` (new, grows through 2.1–2.4)

**Pattern to follow.** Plain stdlib: `dataclasses.dataclass(frozen=True)`, `collections.defaultdict`. No third-party helpers — this package has no dependencies beyond `anki`.

**The data contract (every later subphase and both test files bind to this exactly)**

```python
@dataclass(frozen=True)
class CardDue:
    card_id: int   # Anki card id
    day: int       # absolute due day number, i.e. the review-queue `due` column
    ivl: int       # current interval in days, used only as a move-selection tiebreak
```

- `plan_rebalance(...) -> RebalanceResult` (see 2.5), whose `moves` field maps `card_id -> new_day`, containing **only cards that actually move**. A card whose day is unchanged is absent from the mapping.
- Buckets are `dict[int, list[int]]` — day number to the list of card ids on it, each list kept in a stable canonical order (**ascending `card_id`**). The two passes each impose their own selection order when picking movers; the buckets themselves are not pre-sorted by either.

**`RunState` — the single mutable object every pass operates on.** Buckets hold bare card ids, but the selection orders need `ivl`, the shift cap needs each card's *original* day, and the untouched-first preference (D6.3) needs to know which cards have already moved. Rather than thread five parallel dicts through four functions, all of it lives in one state object built once by `plan_rebalance`. **This is the whole contract; nothing re-derives any of it from a card id.**

```python
@dataclass
class RunState:
    buckets: dict[int, list[int]]   # day -> card ids on it, kept ascending by card_id
    ivl_by_id: dict[int, int]       # card_id -> ivl
    origin_by_id: dict[int, int]    # card_id -> its ORIGINAL day, before any pass ran
    moved: set[int]                 # card ids that have moved at least once THIS RUN
    start_day: int                  # window start; nothing is ever placed before it
    end_day: int                    # MUTABLE — the reverse pass (2.3) may extend it
    max_shift: int | None           # cap on EARLIER displacement from origin; None = uncapped
```

Every signature, stated once and binding on 2.2–2.5 and both test files:

```python
def build_buckets(cards: Sequence[CardDue], start_day: int) -> dict[int, list[int]]: ...

# Selection orders — take card ids plus the state, never CardDue.
def max_move_order(card_ids: Sequence[int], state: RunState) -> list[int]: ...
def min_move_order(card_ids: Sequence[int], state: RunState) -> list[int]: ...

# Shared mutation primitives — the ONLY way a card changes day.
def may_move_to(card_id: int, target_day: int, state: RunState) -> bool: ...
def move_card(card_id: int, from_day: int, to_day: int, state: RunState) -> None: ...

# The three passes. Each mutates `state` in place and returns None.
def apply_max_pass(state: RunState, max_per_day: int) -> None: ...
def apply_reverse_max_pass(state: RunState, max_per_day: int) -> None: ...
def apply_min_pass(state: RunState, min_per_day: int) -> None: ...

def plan_rebalance(
    cards: Sequence[CardDue],
    start_day: int,
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None = 14,
    set_earlier: bool = False,
) -> RebalanceResult: ...
```

`plan_rebalance` is the only function that ever sees `Sequence[CardDue]`. It builds `ivl_by_id = {c.card_id: c.ivl for c in cards}`, `origin_by_id = {c.card_id: c.day for c in cards}`, `moved = set()`, derives `end_day`, and assembles the `RunState`. A card id absent from `ivl_by_id` or `origin_by_id` is a programming error: let it raise `KeyError` rather than defaulting, so a threading mistake fails loudly instead of silently ordering everything as `ivl=0`.

**`may_move_to(card_id, target_day, state)`** — the shift-cap gate (D6.1). Returns `False` if either:
- `target_day < state.start_day` — nothing is ever placed before the window start (D2, absolute), or
- `state.max_shift is not None and target_day < state.origin_by_id[card_id] - state.max_shift` — the card would end up more than `max_shift` days earlier than where it *originally* sat.

The cap is measured **cumulatively from the card's origin**, not per hop, so a card cannot creep past it via repeated one-day moves. Moving a card **later** is never blocked by the cap (2.3 relies on this).

**`move_card(card_id, from_day, to_day, state)`** — the only mutation primitive. Removes the id from `state.buckets[from_day]`, inserts it into `state.buckets[to_day]` keeping that list ascending by `card_id`, adds the id to `state.moved`, and creates `state.buckets[to_day]` (extending `state.end_day`) if the day does not yet exist. **A card is in `state.moved` from its first move onward, even if a later move returns it to its origin day.** `move_card` performs no legality check of its own.

**Who must call `may_move_to` first — scoped, not universal.** Only the passes that move a card **earlier** (2.2 and 2.4) must gate every move through `may_move_to`. The reverse pass (2.3) moves cards **later** and deliberately does not consult it: the shift cap constrains earlier displacement only, and a later move cannot cross the `start_day` floor. This is the single rule; 2.3's "not consulted here" is an instance of it, not an exception to it.

**The two horizon bounds, defined here once (both passes and all post-conditions refer to them):**
- **`start_day`** — the first day of the rebalance window, supplied by the caller. 3.3 computes it as `col.sched.today + args.start_offset` (default offset `1`, decision D2). No card is ever placed before it.
- **`end_day`** — **the maximum `day` among the input `cards`**, computed inside `plan_rebalance`, *not* a parameter. When `cards` is empty, both passes are skipped and the result is empty. This definition is load-bearing for a blind test author: `end_day` is derived from the data, never passed in.

**Work**
- `validate_bounds(min_per_day: int | None, max_per_day: int | None) -> None`, raising `ValueError` with a specific message for each case:
  - both `None` → *"at least one of --min or --max must be given"*
  - `min_per_day is not None and min_per_day < 0` → error
  - `max_per_day is not None and max_per_day < 1` → error
  - both given and `min_per_day > max_per_day` → error
- `build_buckets(cards: Sequence[CardDue], start_day: int) -> dict[int, list[int]]` — group by `day`, **clamping nothing and dropping nothing**. Every day in `[start_day, end_day]` gets a key, including empty ones, so downstream sweeps do not have to test for missing keys. Each list is sorted **ascending by `card_id`** — a stable canonical order, not a selection order.
  **Out-of-range input:** a card with `day < start_day` is a caller error. `build_buckets` **raises `ValueError`** naming the offending card id and day; it does not silently clamp, drop, or create a key below `start_day`. 3.1 filters such cards out before calling, so this never fires in production — but it is a defined, testable behaviour rather than an open question.

**Two selection orders, both untouched-first (decisions D5a, D5b, D6.3).** Each order is a **two-level sort**: the settled D6.3 preference *"cards already moved this run stay put"* is the PRIMARY key, and the pass's `ivl` heuristic is only the tiebreaker within each group.

```python
# max_move_order — used by 2.2 and 2.3
key = (card_id in state.moved, -state.ivl_by_id[card_id], card_id)

# min_move_order — used by 2.4
key = (card_id in state.moved, +state.ivl_by_id[card_id], card_id)
```

`False < True` in Python, so untouched cards sort first automatically — that is the whole mechanism, and it must not be written any other way.

- **Primary key — untouched before moved (D6.3).** A card that has already moved this run is chosen last. The user's example: a day holding 22 cards of which 6 arrived by an earlier shift, needing 6 movers, picks 6 of the **16 untouched** and leaves the 6 arrivals alone.
- **Tiebreaker for the max passes — largest `ivl` first (D5a).** Every max-pass move is exactly one day, so the disturbance is fixed and tiny; giving it to the longest-interval card makes it proportionally smallest.
- **Tiebreaker for the min pass — smallest `ivl` first (D5b).** The min pass can advance a card a long way, so it takes the cards that are cheapest to advance proportionally.
- **Final tiebreak `card_id` ascending** — determinism is a hard requirement for both.

**The preference is NOT an invariant, and the passes must not treat it as one.** When a day's untouched cards are exhausted, already-moved cards are selected and move again. The user's example: after 17 cards are pushed from day 10 to day 9, one of those just-arrived cards may legitimately cascade on to day 8, because the max constraint outranks the preference. Any implementation that refuses to move an already-moved card is wrong.

**Acceptance criteria**
- `validate_bounds` raises on each of the four invalid combinations and returns `None` on: min only, max only, both with `min <= max`, and `min == max`.
- `build_buckets` over `[CardDue(1, 10, 5), CardDue(2, 10, 90), CardDue(3, 12, 1)]` with `start_day=10` yields keys `{10, 11, 12}`, with `11` mapping to an empty list and `10` mapping to `[1, 2]` (canonical ascending `card_id`).
- `end_day` for that same input is `12`, derived from the data.
- `build_buckets` raises `ValueError` for a card with `day` below `start_day`.
- With `state.moved` empty, `max_move_order` on day 10 of that input returns `[2, 1]` (ivl 90 before ivl 5) and `min_move_order` returns `[1, 2]` (ivl 5 before ivl 90). **The two orders are exact reverses on this input** — one test asserting both catches any accidental sharing of a single heuristic.
- With `state.moved == {2}`, `max_move_order` on day 10 returns `[1, 2]` — the untouched low-`ivl` card now outranks the moved high-`ivl` one. **This is the test that proves the untouched-first key is primary and not merely a tiebreak.**
- With `state.moved == {1, 2}` (all moved), both orders fall back to their pure `ivl` ordering — proving the preference degrades rather than blocking movement.
- Ties: two cards with identical `ivl` and identical moved-status order by ascending `card_id` under *both* orders.
- `may_move_to` returns `False` below `start_day`; `False` when `max_shift=14` and the target is more than 14 days before the card's `origin_by_id` value; `True` at exactly 14 days earlier (the cap is inclusive); `True` for any later-day target regardless of the cap.
- `move_card` adds the card to `state.moved`, keeps the destination list ascending by `card_id`, and extends `state.end_day` when the destination is a new day beyond it.

**Test approach — oracle: `new contract tests`.** `tests/test_due_plan.py`, pytest, table-driven via `@pytest.mark.parametrize` for the validation matrix.

---

#### 2.2: Max pass — descending sweep, one-day cascade earlier, shift cap

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

**Work.** `apply_max_pass(state, max_per_day) -> None`, mutating `state` in place. Called only when `max_per_day is not None`.

```
for d from state.end_day down to state.start_day + 1:
    excess = len(state.buckets[d]) - max_per_day
    if excess <= 0: continue
    moved_here = 0
    for cid in max_move_order(state.buckets[d], state):
        if moved_here == excess: break
        if may_move_to(cid, d - 1, state):
            move_card(cid, d, d - 1, state)
            moved_here += 1
    # moved_here < excess means the shift cap blocked the rest;
    # day d stays over max, and 2.5 treats that as infeasibility.
```

**Moves NEVER skip days (settled D6.2).** The target is **always exactly `d - 1`** — even when day `d-1` already sits inside `[min, max]` and the arrival pushes it over. **Do not search for the nearest earlier day with free capacity**; that behaviour is explicitly rejected. The receiving day's own excess is handled when the descending sweep reaches it one step later, which is precisely why the sweep runs backwards. The user's example: overflow from day 10 goes to day 9 even if day 9 is in range and the arrival puts it over.

**Selection is untouched-first (settled D6.3).** `max_move_order` puts never-yet-moved cards ahead of cards that already moved this run, with largest `ivl` as the tiebreaker. A card that arrived from day `d+1` may still be moved on to `d-1` when day `d` has too few untouched cards to cover its excess — the cap outranks the preference.

**The shift cap is enforced through `may_move_to` (settled D6.1)** and is measured cumulatively from `origin_by_id`, so a card cannot creep past it one hop at a time. When the cap blocks every remaining candidate, the day stays over max; 2.2 does not raise — it leaves the state for 2.5 to judge.

**Why descending, and why it terminates.** The sweep starts from the latest day exactly as the request states. Every move strictly decreases a card's day, days are bounded below by `start_day`, and each day is visited once, so the pass terminates.

**Why `start_day + 1` is the lower bound.** `start_day` has nothing earlier to push to; it is the sink.

**Acceptance criteria**
- `max=2`, `start_day=1`, days 1..3 holding counts `[0, 0, 5]` → final `[1, 2, 2]`. Trace: day 3 sheds 3 onto day 2 (`[0,3,2]`), then day 2 sheds 1 onto day 1.
- `max=16`, `start_day=1`, counts `[0, 0, 40]` → final `[8, 16, 16]`, sink overflow `0`.
- Sink overflow: counts `[0, 0, 60]`, `max=16` → final `[28, 16, 16]`, sink overflow `12`.
- **One-day rule, direct test — assert on card IDENTITY, never on double-movement.** `max=3`, `start_day=1`, day 2 holding 3 cards and day 3 holding 6. Final counts are `[3, 3, 3]` under *either* implementation, so counts prove nothing; the origins of the cards do:
  - **Correct (one-day rule):** day 3 sheds 3 onto day 2 — *even though day 2 is already at max* — making it `[0, 6, 3]` mid-sweep. When the sweep reaches day 2, its excess of 3 is drawn from `max_move_order`, whose **primary key is untouched-first**, so it selects day 2's own three originals. **Assert: day 1 holds exactly the three cards that started on day 2, and day 2 holds exactly the three that started on day 3.**
  - **Wrong ("nearest day with room"):** day 3's overflow skips past the full day 2 and lands directly on day 1, so day 1 would hold the original *day-3* cards and day 2's originals would never move.
  - **Every card moves at most ONCE in this scenario** — assert that too. Under settled D6.3 the untouched-first key guarantees no card is picked twice here, so an assertion that some card "passed through day 2" or "changed day twice" is **unsatisfiable and must not be written**. (An earlier draft of this plan asserted exactly that; it was wrong, and a red test from it would tempt a coder into breaking D6.3.)
- **Untouched-first, direct test:** a day over max holding some cards already in `state.moved` picks the untouched ones first; only when untouched cards run out does an already-moved card get selected.
- **Shift cap:** with `max_shift=1`, a card originating on day 10 can reach day 9 but not day 8; a day whose cards are all cap-blocked stays over max and `apply_max_pass` returns normally without raising.
- **No card moves later**, **no card lands below `start_day`**, **multiset preserved** (same card ids before and after, no duplicates).
- Idempotence: a second run over an already-conforming distribution produces no moves.
- Determinism: same input, same output, repeatedly.

**How a 2.2 test computes sink overflow.** `apply_max_pass` returns `None`; the `sink_overflow` *field* lives on `RebalanceResult` (2.5). At this level derive it from the mutated state:

```python
sink_overflow = max(0, len(state.buckets[state.start_day]) - max_per_day)
```

**Test approach — oracle: `new contract tests`.** Build a `RunState` directly; assert per-day counts and the invariants above. Hand-built distributions only — do not pull in `hypothesis`, it is not a dependency of this repo.

---

#### 2.3: Reverse max pass — ascending sweep, one-day cascade later, horizon extension

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

**Why this exists (settled D3).** By default cards move in one direction only — earlier — and when `--max` cannot be satisfied that way the run **fails** rather than writing a partial result. `--set-earlier` (default `false`) opts into the escape hatch the user described as *"reverse the process"*: run the normal earlier pass first, and if excess is still piled up at the window start, mirror the whole procedure — sweep from the front, push excess **later** one day at a time, extending past the current last day as needed — so the run succeeds instead of failing.

**Work.** `apply_reverse_max_pass(state, max_per_day) -> None`, mutating in place. Called by 2.5 **only** when the max pass left days over `max_per_day` **and** `set_earlier` is true.

```
d = state.start_day
while True:
    excess = len(state.buckets[d]) - max_per_day
    if excess > 0:
        for cid in max_move_order(state.buckets[d], state)[:excess]:
            move_card(cid, d, d + 1, state)   # creates day d+1 and extends end_day if needed
    if d >= state.end_day and len(state.buckets.get(d + 1, [])) == 0:
        break
    d += 1
```

**Exact mirror of 2.2.** Same one-day rule (target is always `d + 1`, never a search for a day with room), same untouched-first selection with the D5a `ivl` tiebreaker, same cascade — only the direction and sweep order are flipped.

**`may_move_to` is NOT consulted here.** The shift cap governs how far a card may be pulled *earlier*; moving later is never cap-blocked (2.1 states this explicitly). The `start_day` floor is also irrelevant — this pass only increases days.

**Horizon extension.** `move_card` creates `state.buckets[d + 1]` when it does not exist and raises `state.end_day` accordingly. Every later stage — the min pass (2.4) and the post-conditions (2.5) — must read the **updated** `state.end_day`, not a value captured before this pass ran.

**D2 still holds absolutely.** This pass only ever moves cards later, so nothing can land on today or earlier. The window start remains untouchable in both directions.

**Why it terminates.** Each day is finalized at `<= max_per_day` before the sweep advances, and cards only move forward into a finite total. The loop ends at the first day at or beyond `end_day` with nothing spilling past it.

**Acceptance criteria**
- Continuing 2.2's sink-overflow case: `[28, 16, 16]` with `max=16` → `[16, 16, 16, 12]`, `state.end_day` extended from 3 to 4, total still 60.
- Multi-day cascade: `[40, 0, 0]` with `max=16` → `[16, 16, 8]`, no extension needed beyond day 3.
- Extension beyond the original horizon: `[50]` (single day) with `max=16` → `[16, 16, 16, 2]` across days 1..4, `end_day == 4`.
- **Cards move LATER here** — assert new day > old day for every card this pass moves, the one place in the plan where that is legal.
- The shift cap does not block this pass: with `max_shift=0`, the reverse pass still moves cards later normally.
- Nothing lands on or before `start_day - 1`; the day-`start_day` count ends at exactly `max_per_day` when it began above it.
- Multiset preserved; deterministic.

**Test approach — oracle: `new contract tests`.**

---

#### 2.4: Min pass — ascending sweep, deficits filled from later days, shift cap

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

**Work.** `apply_min_pass(state, min_per_day) -> None`, mutating in place. Called only when `min_per_day is not None`, and always **after** the max passes.

```
for d from state.start_day up to state.end_day:
    if every day > d is empty: break          # the tail: stop enforcing min
    deficit = min_per_day - len(state.buckets[d])
    if deficit <= 0: continue
    repeat deficit times:
        picked = None
        for s in ASCENDING order over every non-empty day in (d, state.end_day]:
            for cid in min_move_order(state.buckets[s], state):
                if may_move_to(cid, d, state):
                    picked = (cid, s); break
            if picked is not None: break       # nearest LEGAL source wins
        if picked is None: break               # no card ANYWHERE can legally reach d
        move_card(picked.cid, picked.s, d, state)
```

**The source is the NEAREST non-empty later day — no surplus-hunting.** An earlier draft preferred a day with a surplus above `min` so as to leave at-minimum days undisturbed. That is exactly the kind of skip-ahead search D6.2 rejects, so it is gone: take from `d + 1`, or from the nearest later day that has anything at all. A source day drained below `min` is repaired when the ascending sweep reaches it.

**Consistency with the one-day rule.** Pulling from day `s` to day `d` looks like a multi-day jump, but every day strictly between them is empty by construction (`s` is the *nearest* non-empty day), so walking the card back one day at a time lands it in exactly the same place. The two formulations are observationally identical; implement the direct move.

**Selection is untouched-first (D6.3), then smallest `ivl` (D5b).** `min_move_order` supplies both keys. A card already moved this run is taken only when the source day has no untouched card that clears the cap.

**A cap-blocked candidate is skipped, NOT a reason to abandon the day (settled).** The search is over *(source day, card)* pairs, not over source days alone: if the nearest non-empty day offers no card that clears `may_move_to`, try the remaining cards on that day, then move outward to the next non-empty day, and so on. Day `d` is left short **only when no card on any later day can legally reach it**.

This case is reachable, not theoretical. The max pass deposits far-out cards onto early days one hop at a time, so day `d+1` can hold cards with a high `origin_by_id` while `d+2` holds cards sitting on their origin. With `max_shift=14`, a card on day 2 whose origin is 16 fails `may_move_to(cid, 1, …)` because `1 < 16 - 14`, while a card on day 3 whose origin is 3 passes easily. Giving up at day 2 would leave day 1 short with a perfectly legal source one day further out — a silent, deterministic under-fill.

**When the search genuinely exhausts, the shortfall is legitimate (settled D6.1).** Day `d` stays below `min`, the pass moves on, and 2.5 collects it into `short_days`. **This is not a failure** — it is the user's stated consequence of capping, reported and never asserted away.

**Why ascending, why the tail is exempt, why it cannot break `max`.** Sweeping forward lets a drained source day repair itself from further out. Once no cards remain beyond `d`, `d` is simply where the queue ends — a short trailing day is not a violation, and without the `break` guard the sweep would try to conjure cards from nothing. And because this pass fills only *up to* `min_per_day`, with `validate_bounds` guaranteeing `min <= max`, it can never push a day above `max` or undo the max passes.

**Acceptance criteria**
- `min=8`, counts `[3, 20, 20, 20]` → `[8, 15, 20, 20]` (day 1 pulls 5 from day 2).
- Cascade through an at-minimum day: counts `[0, 8, 20]`, `min=8` → final `[8, 8, 12]`. **Day 2 IS disturbed**: it gives its 8 to day 1 and refills from day 3. Assert the final counts *and* that day 2's cards are not the same ids it started with — this is the test that proves surplus-hunting was removed.
- No-surplus cascade: counts `[0, 8, 8]`, `min=8` → `[8, 8, 0]`.
- Tail exemption: counts `[8, 3]`, `min=8` → **no moves**, nothing lies beyond day 2.
- **Shift cap leaves a day short:** `min=8`, counts `[0, 20]` with `max_shift=0` → no moves at all (no card may move earlier), day 1 stays at 0, and the pass returns normally.
- **Keeps hunting past a cap-blocked source — the N17 case.** `min=8`, `max_shift=14`, `start_day=1`. Day 1 empty; day 2 holds cards whose `origin_by_id` is 16 (so `may_move_to(cid, 1, …)` is `False`, since `1 < 16 - 14`); day 3 holds untouched cards whose origin is 3 (legal). **Assert day 1 is filled from day 3, not left short**, and that day 2's cap-blocked cards are untouched. A implementation that abandons day 1 at the first blocked source fails this and only this criterion.
- Untouched-first: a source day holding both moved and untouched cards yields its untouched ones first.
- **No card moves later**, no card below `start_day`, multiset preserved, deterministic.

**Test approach — oracle: `new contract tests`.**

---

#### 2.5: `plan_rebalance` orchestration, infeasibility handling, post-conditions

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

**Work.** `plan_rebalance(cards, start_day, min_per_day, max_per_day, max_shift=14, set_earlier=False) -> RebalanceResult`.

Sequence, in exactly this order:

1. `validate_bounds(min_per_day, max_per_day)`.
2. If `cards` is empty, return immediately — no passes, no exception — with **every field explicitly defined** (a blind test author must not have to guess any of them): `moves={}`, `before={}`, `after={}`, `sink_overflow=0`, `short_days=[]`, `reverse_pass_used=False`, and **`end_day = start_day - 1`**. That last value is deliberate rather than arbitrary: `end_day` is normally the maximum `day` among the input cards, which is undefined for an empty input, and `start_day - 1` makes `range(start_day, end_day + 1)` the empty range — so every post-condition loop and every histogram walk traverses nothing without needing an empty-input special case.
3. Build the `RunState` (2.1): buckets, `ivl_by_id`, `origin_by_id`, `moved=set()`, `start_day`, derived `end_day`, `max_shift`.
4. If `max_per_day is not None`:
   - `apply_max_pass(state, max_per_day)`
   - compute `over_max = [d for d in range(start_day, state.end_day + 1) if len(state.buckets[d]) > max_per_day]`
   - if `over_max` is non-empty:
     - **`set_earlier` false → raise `InfeasibleRebalance`** (below). Nothing is written; the caller exits non-zero.
     - **`set_earlier` true → `apply_reverse_max_pass(state, max_per_day)`**, then recompute `over_max`; if it is *still* non-empty, raise `InfeasibleRebalance` (this should not happen, since the reverse pass has unbounded horizon, and a raise here is a genuine bug signal).
5. If `min_per_day is not None`: `apply_min_pass(state, min_per_day)`.
6. Compute the result fields and run the post-condition checks.

**Why max before min.** Max is the hard cap; min-filling can never violate it (2.4). The reverse order would let max-relief undo min-filling.

**`InfeasibleRebalance(Exception)`** — a new exception type carrying the offending days and their counts, plus the reason (`sink overflow` vs `shift cap`). This is a *user-facing* condition, not a bug: 3.3 catches it, prints which days cannot be brought under `--max` and suggests `--set-earlier` or a larger `--max-shift`, and exits non-zero **with nothing written to the collection**.

**`RebalanceResult`** — frozen dataclass:
- `moves: dict[int, int]` — `card_id -> new_day`, changed cards only
- `before: dict[int, int]`, `after: dict[int, int]` — per-day counts for 3.2's histogram
- `end_day: int` — the final horizon, which the reverse pass may have extended past the input maximum
- `sink_overflow: int` — how far `start_day` exceeded `max_per_day` after the earlier-only max pass, `0` otherwise; retained for reporting even when the reverse pass resolved it
- `short_days: list[int]` — days left below `min_per_day` that are **not** in the exempt tail. Non-empty is **legal** when `max_shift` blocked the fills (D6.1); it is reported, never asserted away.
- `reverse_pass_used: bool` — whether `--set-earlier` actually fired, so 3.2 can say so loudly in the summary

**Post-conditions** — raise `AssertionError` (a bug signal, not a user error) if violated:
1. **No card lands below `start_day`.** Absolute, both modes (D2).
2. If `set_earlier` is false: **every moved card's new day is strictly less than its old day.** If `set_earlier` is true this is relaxed — the reverse pass legitimately moves cards later — and is replaced by: no card moved later *unless* `reverse_pass_used` is true.
3. If `max_per_day` given: **every day in `[start_day, end_day]` holds at most `max_per_day`.** Note this now includes `start_day`, because the only ways it could be over are the two that already raised `InfeasibleRebalance`.
4. **Shift cap respected:** for every card, `new_day >= origin_by_id[card_id] - max_shift` when `max_shift is not None`.
5. **Multiset preserved** exactly — same card ids, no duplicates, none lost.
6. `min_per_day` is deliberately **NOT** a post-condition assertion — `short_days` reports it instead, because the cap makes shortfall legal.

**Acceptance criteria**
- Post-conditions 1–5 hold for: max-only, min-only, and both-given inputs.
- **The user's real case, run with `set_earlier=True`** — `min=8, max=16, max_shift=14, set_earlier=True` over the back-loaded distribution `[0, 40, 2, 0, 25, 1]` (68 cards, `start_day=1`, `end_day=6`). Traced end to end against this plan's own pseudocode:
  - max pass → `[24, 16, 2, 9, 16, 1]`, so `sink_overflow == 8` and `over_max == [1]`
  - reverse pass → **`[16, 16, 10, 9, 16, 1]`**, `reverse_pass_used is True`, `end_day` stays `6` (no extension needed), total still 68
  - min pass → **no moves**: days 1-5 are all at or above 8, and day 6 is the exempt tail, so `short_days == []`
  - all post-conditions hold, and `before`/`after` sum to the same total

  **This criterion MUST specify `set_earlier=True`.** With the default `set_earlier=False` the same input raises `InfeasibleRebalance` at step 4 — no `RebalanceResult` exists and nothing can be asserted about post-conditions. That is the settled D3 behaviour working correctly, not a defect, and it is why this criterion doubles as the reverse pass's realistic end-to-end exercise.
- **Default infeasibility:** a distribution whose max pass leaves `start_day` over `max` with `set_earlier=False` raises `InfeasibleRebalance`, and the exception names the offending days.
- **`set_earlier=True` rescues the same input:** no exception, `reverse_pass_used is True`, every day at or under `max`, and `end_day` extended.
- **Cap-induced shortfall is reported not raised:** `min=8, max_shift=0` over a sparse distribution returns normally with `short_days` non-empty.
- Empty input returns `moves == {}`, `before == {}`, `after == {}`, `end_day == start_day - 1`, `sink_overflow == 0`, `short_days == []`, `reverse_pass_used is False`, and raises nothing; a single card returns no moves.
- `sink_overflow > 0` exactly when the earlier-only max pass had nowhere earlier to put a card — **observable only with `set_earlier=True`.** In default mode that same condition raises `InfeasibleRebalance`, so no `RebalanceResult` is ever returned carrying a positive value. Write this case in `--set-earlier` mode; a default-mode version of it can only ever assert the exception.
- Determinism across repeated runs on identical input.

**Test approach — oracle: `new contract tests`.**

---

### Phase 3: Anki collection adapter & CLI (`rebalance_due.py`)

#### 3.1: Collection open/close, deck+subdeck resolution, card extraction

**File scope**
- `libs/python/anki-tools/anki_tools/rebalance_due.py` (new)
- `libs/python/anki-tools/tests/test_rebalance_due.py` (**new, created in THIS subphase**)

**The test file is not optional and cannot be deferred to 4.1.** `~/.claude/hooks/smart-test.sh` (`run_python_tests`) hard-blocks — prints *"Missing required test file"* and returns exit 2 — on the first write of a non-test `.py` that has no matching test file, and one of the paths it searches is exactly `<dir>/../tests/test_<base>.py`, i.e. `libs/python/anki-tools/tests/test_rebalance_due.py`. Writing `rebalance_due.py` without it will fail immediately. Create the test file in the same packet, covering this subphase's functions; **4.1 extends the same file** rather than creating it. (`anki_tools/__init__.py` is exempt from that hook — its basename matches the hook's `^(__init__|__main__|setup|conf|config|settings)$` allowance — which is why 1.1 needs no paired test.)

**Pattern to follow.** `libs/python/anki-tools/anki_tools/get_deck_info.py` — the shape of `get_anki_collection_path()`, the guarded `Collection(path)` open with the *"Make sure Anki is not running"* hint, and the `col.close()` at the end. **Locate these by symbol name; the formatter moves line numbers.**

**First line of the file:** `#!/usr/bin/env python3` (Conventions / `EXE002`).

**Work**
- `get_anki_collection_path()` — same platform switch as `get_deck_info.py`'s function of that name.
- `resolve_deck_ids(col, deck_name) -> list[DeckId]` — `col.decks.id_for_name(deck_name)`; if `None`, raise a clear error naming the deck. Then `col.decks.deck_and_child_ids(deck_id)`, which returns the deck **plus every descendant** (verified above). Deck-name matching is **believed** case-insensitive, but attribute the claim correctly: `id_for_name` (`decks.py:147`) has **no docstring** — it is a bare backend call returning `None` on `NotFoundError`. The *"Get deck with NAME, ignoring case"* docstring belongs to its sibling `by_name` (`decks.py:254`), which delegates to `id_for_name`, so case-insensitivity is a reasonable inference about the backend rather than a documented property of the function used here. **Verify it in this subphase** — a two-line probe against the temp collection resolving `"PROGRAMMING::CODING"` — and echo the resolved deck names in the error path either way, so a near-miss name is never silently treated as absent.
- `collect_cards(col, deck_ids, start_day) -> list[CardDue]` — **enumerate via `col.decks.cids(did, children=False)` for each `did` in `deck_ids`** (the subdeck expansion already happened in `resolve_deck_ids`, so do not also pass `children=True` or cards would be counted twice). Include a card only if **all** of:
  - `card.queue == 2` and `card.type == 2` (review queue; `due` is an absolute day number here — see the `anki/cards.py` header comment quoted above)
  - `card.odid == 0` (not in a filtered deck; a filtered card's real due lives in `odue` and rewriting it is unsafe)
  - `card.due >= start_day`

  **The `odid` guard is defensive, not load-bearing under this enumeration route** — and the skip report must not pretend otherwise. A card pulled into a filtered deck carries the *filtered* deck's id in `did` and the original deck's id in `odid`, so enumerating by `did ∈ deck_ids` never returns it: the guard can never fire and a "0 filtered" counter would read zero even when the deck genuinely has cards sitting in a filtered deck. Keep the guard (it becomes live if the enumeration ever switches to the `find_cards('deck:"…"')` alternative), but **do not emit a filtered counter**; instead state plainly in the report that *filtered-deck cards are not visible to this route and are left untouched*.

  Everything else excluded is counted by reason and reported, e.g. "skipped 12 new, 3 learning, 5 suspended, 88 already due or overdue; filtered-deck cards are not visible to this route". Silent exclusion is not acceptable.
- `start_day` is computed by the caller as `col.sched.today + args.start_offset` (default offset `1` — see decision D2).

**Acceptance criteria**
- Against a synthetic collection with `programming::coding` and `programming::coding::python`, `resolve_deck_ids` returns both ids and not the unrelated `programming` parent or `Default`.
- A nonexistent deck name produces a non-zero exit with a message naming the deck, not a traceback.
- `collect_cards` returns only review-queue cards with `due >= start_day`, and the skip counters sum with the returned count to the total card count in those decks.
- The collection is closed on both the success and the error path.
- **No `except Exception` and no `# noqa` anywhere in the file** — the Anki failure path catches `anki.errors.DBError` and `anki.errors.AnkiException` (Conventions). A grep for `except Exception` in `rebalance_due.py` returns nothing.
- The file starts with `#!/usr/bin/env python3`.

**Test approach — oracle: `new contract tests`.** `tests/test_rebalance_due.py` is created here with a first slice covering `resolve_deck_ids` and `collect_cards` against a temp collection built as 4.1 describes. 4.1 then extends the same file with the end-to-end cases.

---

#### 3.2: Apply moves via `set_due_date`, backup, dry-run histogram

**File scope**
- `libs/python/anki-tools/anki_tools/rebalance_due.py`

**Work**
- `render_histogram(before, after, min_per_day, max_per_day) -> str` — one line per day: day offset from today, the before count, the after count, and a marker for any day still outside the bounds. Reuse the `pdash()` separator idiom from `get_deck_info.py:39-40` for section rules.
- `apply_moves(col, moves, today) -> int` — **group the moves by target day** and issue one call per day:
  `col.sched.set_due_date(cids_for_day, str(target_day - today))`.
  Use the **non-bang** form. Verified above: `"5"` sets `due = today + 5` and leaves `ivl` untouched on a review card, whereas `"5!"` overwrites `ivl` with the delay. Preserving the interval is the whole point — we are moving *when* a card is seen, not rewriting its scheduling state (decision D4).
  Do **not** write `card.due` directly and call `col.update_card`; `set_due_date` goes through the backend op, which handles `mod`/`usn` bookkeeping and registers an undo entry.
- Backup before any write, unless `--no-backup`:
  `col.create_backup(backup_folder=<dir>, force=True, wait_for_completion=True)`
  with `<dir>` defaulting to `<collection dir>/backups` (verified as the profile's real backup location, currently holding `.colpkg` files). Note the documented catch: it returns `False` when `force=True` if the collection is unchanged — treat `False` as informational, not as failure.
- Dry-run path writes nothing, takes no backup, and prints the histogram plus a per-day move summary.
- **Order of operations is a safety property, not a detail.** `plan_rebalance` runs to completion *before* the backup is taken and before any `set_due_date` call. An `InfeasibleRebalance` (2.5) therefore aborts with the collection untouched and no backup churn — the settled D3 guarantee of "exits non-zero with nothing written" depends on this ordering.
- When `result.reverse_pass_used` is true, the summary must say **explicitly** that some cards were moved to LATER dates and show the extended horizon. That is the one behaviour a user opting into `--set-earlier` most needs confirmed before answering the `y/N` prompt.
- The histogram covers `start_day .. result.end_day`, reading the **post-pass** horizon, and flags any day in `result.short_days` as under-min-by-cap rather than silently showing a low count.

**Acceptance criteria**
- After `apply_moves`, re-reading each moved card from the collection shows `due` equal to the planned absolute day and `ivl` **unchanged** from before the call.
- Number of `set_due_date` calls equals the number of distinct target days, not the number of cards.
- `--dry-run` leaves the collection byte-identical (compare mtime/size or reopen and re-read the same cards).
- With backups enabled, a new file appears in the backup folder before any card is modified.
- The histogram sums to the same card total before and after.

**Test approach — oracle: `new contract tests`** (driven by 4.1).

---

#### 3.3: argparse CLI wiring and argument validation

**File scope**
- `libs/python/anki-tools/anki_tools/rebalance_due.py`

**Pattern to follow.** `anki_tools/get_deck_info.py`'s `main()` + `if __name__ == "__main__": main()`; `anki_tools/build_deck.py`'s `argparse` usage — but use `parser.parse_args()`, **not** `parse_known_args()`, which is the latent bug in `build_deck.py` and `web-crawlers`.

**Interface**

```
anki-rebalance-due DECK [--min N] [--max N] [--max-shift N] [--set-earlier]
                        [--dry-run] [--yes] [--start-offset N]
                        [--collection PATH] [--backup-dir PATH] [--no-backup]
```

- `DECK` — positional, required. Full Anki deck name including `::` separators, e.g. `programming::coding`. Its subdecks are always included.
- `--min N` / `--max N` — both optional individually; **at least one required**. Enforced by calling `validate_bounds` and turning its `ValueError` into `parser.error(...)`, so the failure is a clean usage message and exit code 2, not a traceback.
- `--max-shift N` — **default `14`**. The furthest a card may be moved *earlier* than its own scheduled day, measured cumulatively from where it started (settled D6.1). `--max-shift 0` disables all earlier movement; passing `none` disables the cap entirely. Days that cannot reach `--min` under the cap **stay below min**, and are listed in the summary — that is the documented consequence, not an error.
- `--set-earlier` — **default `false`** (store_true). Off: cards move earlier only, and an unsatisfiable `--max` is a hard failure. On: after the earlier-only pass, a mirrored pass may push excess **later**, extending the horizon, so the run succeeds (settled D3, subphase 2.3). Help text must say plainly that this is the only mode in which a card's due date can move further away.
- `--dry-run` — plan and print, write nothing.
- `--yes` / `-y` — skip the interactive confirmation.
- `--start-offset N` — days after today where the rebalance window begins; **default `1`** (tomorrow). Cards due today or overdue are never touched, in either mode (settled D2).
- `--collection PATH` — override the auto-detected collection path.
- `--backup-dir PATH`, `--no-backup` — see 3.2.
- Default behaviour with none of `--dry-run`/`--yes`: print the histogram, then prompt for confirmation before writing (settled D7).

**Why `--max-shift` defaults to 14.** The user did not fix a number, so this is the plan's proposal and is labelled as such. Two weeks is wide enough to absorb realistic lumpiness — a 40-card clump at `--max 16` spreads over about three days — while being narrow enough to stop `--min` from compacting the entire future queue toward today, which is otherwise its dominant effect (see D6). Anyone wanting the old unbounded behaviour passes `--max-shift none`.

**`InfeasibleRebalance` handling.** Catch it from `plan_rebalance`, print which days cannot be brought under `--max` and why (sink overflow vs shift cap), suggest `--set-earlier` or a larger `--max-shift`, and **exit non-zero with nothing written**. This is a clean user-facing failure, not a traceback.

**Acceptance criteria**
- `anki-rebalance-due programming::coding` with neither `--min` nor `--max` exits non-zero with a message naming both flags.
- `--min 20 --max 16` exits non-zero with a message about min exceeding max.
- `--min 8 --max 16 --dry-run` on the real collection prints a histogram and modifies nothing.
- An infeasible `--max` without `--set-earlier` exits non-zero, names the offending days, mentions both `--set-earlier` and `--max-shift`, and **writes nothing** — assert the collection is unchanged.
- The same input with `--set-earlier` succeeds, and the summary states that cards were moved later.
- `--max-shift` accepts an integer and the literal `none`; the default when the flag is absent is `14`.
- `--help` renders without error and documents that subdecks are included.
- Exit code is `0` on success, non-zero on every validation and runtime failure.
- The file is executable (mode 755) and registered in `package.json` `bin` as `anki-rebalance-due`.

**Test approach — oracle: `new contract tests`** — parser-level tests calling a `build_parser()` factory directly (so the parser is testable without invoking `main()`), plus the 4.1 end-to-end run.

---

### Phase 4: Verification

#### 4.1: End-to-end integration coverage against a synthetic temporary collection

**File scope**
- `libs/python/anki-tools/tests/test_rebalance_due.py` (**extended** — created in 3.1; do not recreate it)

**Pattern to follow.** The probe run during planning proved this whole approach works on 24.06.3 and takes well under a second:

```python
col = Collection(os.path.join(tmp_path, "test.anki2"))
did = col.decks.id("programming::coding")
child = col.decks.id("programming::coding::python")
note = col.new_note(col.models.by_name("Basic"))
note["Front"], note["Back"] = "q", "a"
col.add_note(note, did)
# then force each card into the review queue:
card.type = 2; card.queue = 2; card.due = col.sched.today + N; card.ivl = 30
card.factor = 2500; card.reps = 3
col.update_card(card)
```

**The real user's collection must never be opened by a test.** Use `tmp_path` and close the collection in a fixture teardown.

**Work.** A pytest fixture building a temp collection with a deliberately lumpy distribution across `programming::coding` and its subdeck, plus decoy cards in an unrelated deck, a suspended card, a new card, and a card due in the past. Then drive the full path end to end.

**Acceptance criteria**
- Subdeck cards are included; the unrelated deck's cards are untouched (assert their `due` values are unchanged).
- New, learning, suspended and past-due cards are excluded and appear in the skip report.
- After a real (non-dry-run) apply with `--min 8 --max 16`, re-reading every in-scope card from the collection shows:
  - **No day above 16 anywhere in the window, including the first day.** A *successful* run guarantees this over `start_day..end_day` with no exception, because both routes to an over-max first day already raised `InfeasibleRebalance` and wrote nothing. Do **not** carry over the older "except possibly the sink day" wording — it would let a genuine over-max sink pass the e2e gate.
  - **Every day below 8 appears in the run's reported `short_days`** — do not assert that no such day exists. Under the default `--max-shift 14` a cap-induced shortfall is legal and expected (settled D6.1); the correct check is that each one was *reported*, not that none occurred.
  - every `ivl` unchanged, and no card moved later (this fixture runs in default mode, where the earlier-only invariant is absolute).
- **`card.memory_state` is unchanged** across the apply, asserted alongside `ivl` (R5). Note the plan gate's finding: on non-FSRS review cards `memory_state` is `None`, so this assertion is weak unless the fixture enables FSRS. If enabling FSRS on the temp collection is straightforward, do it and assert properly; if not, record in the exit report that the FSRS path remains unverified rather than claiming coverage.
- `--dry-run` on the same fixture produces the identical histogram but leaves every card's `due` untouched.
- **Default-mode infeasibility, end to end:** a fixture too dense for `--max` within the window exits non-zero, and **every card's `due` is byte-for-byte unchanged** — the settled D3 no-partial-writes guarantee, verified against a real collection rather than only at the unit level.
- **`--set-earlier` end to end:** the same fixture succeeds, some cards land on days later than they started, no card lands on or before today, and the horizon extends past the original last day.
- **`--max-shift` end to end:** with a small cap, no card's new day is more than the cap earlier than its original day, and any resulting under-min days are reported in the output rather than causing a failure.
- **One-day cascade, observable:** a fixture where an over-max day's overflow must pass through an in-range day confirms the receiving day was transiently overfilled and then relieved, not bypassed (settled D6.2).
- The test does not reference `~/.local/share/Anki2` anywhere.

**Test approach — oracle: `new contract tests`.**

---

#### 4.2: No new lint findings, suite green, manual dry-run against the real collection

**File scope** — no source edits; this subphase produces evidence.

**Acceptance criteria**
- **No new lint findings.** `ruff check --output-format=concise .` from `libs/python/anki-tools/` diffed against `ruff-baseline.txt` (captured in 1.1) shows **zero added lines**. The absolute count remains the baseline's 11; **`ruff check .` will still exit non-zero, and that is expected and acceptable** — pre-existing monorepo lint debt is out of scope for this run by the user's decision at the plan gate. Paste both the baseline and the final output into the exit report so the diff is auditable. Same rule for flake8 vs `flake8-baseline.txt`. Do **not** "fix" `build_deck.py`, `get_deck_info.py`, or `mp3_filename_update.py` into this diff.
- `.venv/bin/poetry run pytest` from `libs/python/anki-tools/` is green, with the count of tests reported.
- `pnpm lint` and `pnpm test` from the repo root do not regress versus `pnpm-lint-baseline.txt` / `pnpm-test-baseline.txt` captured in 1.1 Step 0. **`pnpm lint` is expected to remain red** (pre-existing debt, out of scope) — the criterion is *no newly failing package and no new findings*, not a green run. For `pnpm test`, compare only the packages that existed before; `anki-tools` gains its first `test` task in this change and has no comparable "before".
- A manual `--dry-run` against the real collection with `--min 8 --max 16` on `programming::coding`, with Anki closed, producing a histogram pasted into the exit report. **Dry-run only — do not write to the user's real collection as part of the build.** That first real write is the user's call, after reviewing the dry-run output.
- **Scope: the run's product diff contains only files this plan's file scopes name.** Check it as `git -C <parent-worktree> diff --stat <base-branch>...HEAD` **after** restoring hook-reformatted unrelated files — *not* as a bare `git status`, which cannot be clean here. The `PostToolUse` formatter reformats up to ~73 files across every worktree on essentially any write, including writes to paths outside the repo entirely (observed live during planning and again during plan revision). The builder restores those with `git restore <paths>` before reporting; the orchestrator does the same between stages. Only files this plan names may appear in the diff-vs-base.

**Test approach — oracle: `existing suite`** (the suite created in Phases 2–4 plus the lint gate).

---

---

### Phase 5: Scope smart-lint to the triggering file

**Why this phase is in this plan.** It is unrelated to the Anki feature and was added by user order mid-run; it rides this branch and PR #12 because it is small and the branch was already open. Its file scope is disjoint from Phases 1-4, so it cannot interfere with them. **Nothing else about the hook system is in scope** — no other hook, and specifically no change to `smart-test.sh`.

**The problem, measured.** `~/.claude/hooks/smart-lint.sh` runs on every `PostToolUse` Write/Edit and lints the **entire repo** regardless of what was written. Observed repeatedly during this run's planning: a single write — including writes to markdown, and including writes to paths **outside the repo entirely** — reformats ~73 files and emits ~2000 lines of output. It also descends into sibling worktrees under `.workflows/`, so one run's write dirties another run's checkout (this happened to `.workflows/lint-import-audit/`, which ended up with 77 modified files).

**Verified drift — the installed copy is AHEAD of the repo copy.** Confirmed this session with `diff libs/prompting/claude/hooks/smart-lint.sh ~/.claude/hooks/smart-lint.sh` (520 diff lines; repo 591 lines, installed 766):

| | repo copy | installed copy |
|---|---|---|
| `find_pruned()` helper | **absent** (0 references) | present (13 references); prune names at line 88: `node_modules .git vendor target .godot .venv venv env __pycache__ dist build out result .next .turbo`, plus `CLAUDE_HOOKS_PRUNE_EXTRA` |
| config / ignore filenames | `claude-code-hooks-config.sh`, `claude-code-hooks-ignore` | `.claude-hooks-config.sh`, `.claude-hooks-ignore` |
| exit on clean | exits 2 always | exits 0 clean / 2 on issues (lines 754-766) |
| monorepo detection depth | capped | uncapped |
| `TARGET_FILE` | absent | present — bottom block (lines 665-686) parses `.tool_input.file_path // empty` from stdin JSON via `jq`, and also accepts a bare CLI path argument |

**`TARGET_FILE` is already computed but barely used.** It is consumed **only** by the prettier/JS section (lines 489-493 of the installed copy). `lint_python` (line 349) runs `black . --check --exclude …` → `black .` → `flake8 . --exclude=…` repo-wide; `lint_go_modules` (line 298) iterates **every** module running `go vet ./...` (line 335), including modules inside `.workflows/*` worktrees; `lint_rust` (532) and `lint_nix` (594) likewise. The fix is therefore mostly *wiring an existing variable through*, not new machinery.

---

#### 5.1: Scope hook-mode linting to the triggering file

**File scope**
- `libs/prompting/claude/hooks/smart-lint.sh` — **the only product file in this phase**; the sole entry that may appear in the PR diff for Phase 5.
- `~/.claude/hooks/smart-lint.sh` — **an out-of-repo install step, NOT a product file.** It lives outside the repository, will never appear in `git status` or the branch diff, and must not be claimed as a changed file in the exit report. Name it in the report as an install action instead, so the PR gate's `verify-run-scope.sh` (which treats any product change unclaimed by an exit report as a blocking finding) is not confused by a file it cannot see.

**Work, in this order — the order matters.**

1. **Upstream the drift first, before fixing anything.** Replace the repo copy's contents wholesale with the installed copy's. The installed copy is the newer base, so this is an upstreaming of work that already exists, not a rewrite. Do this as its own step so the subsequent scoping change is reviewable as a small diff against a known base rather than being buried inside a 520-line reconciliation.
2. **Apply the scoping fix to that base.**
3. **Install the fixed version** to `~/.claude/hooks/smart-lint.sh`, so both copies end byte-identical.

**The scoping fix — hook mode (`TARGET_FILE` non-empty).**

- **Early clean exit.** If the file does not exist, is outside the repo root the hook is running in, matches `.claude-hooks-ignore`, or has no lintable extension (`.py .go .js .jsx .ts .tsx .rs .nix`) → print **one short line** and `exit 0` immediately. This is the clause that stops markdown writes, progress-log writes, and writes to paths outside the repo from triggering a full sweep — the single largest source of the observed cost.
- **`.py`** → `black --check` then format **that file only**; `flake8` **that file** with the same computed args the repo-wide path builds; `ruff` on that file only, if the repo copy's `ruff check --fix .` step survives the upstreaming.
- **`.go`** → `gofmt` that file; `go vet` **only the module containing it** (nearest enclosing `go.mod`), never all modules.
- **`.js/.jsx/.ts/.tsx`** → keep the existing per-file prettier behaviour already implemented at lines 489-493.
- **`.rs`** → fmt/clippy only the crate containing the file.
- **Language sections whose type does not match `TARGET_FILE` are skipped entirely** — no project-type detection sweep at all in hook mode.

**The scoping fix — CLI mode (`TARGET_FILE` empty; tty or manual invocation).**

Repo-wide behaviour is **unchanged**, with exactly one addition: add **`.workflows`** to `find_pruned`'s prune list (line 88) so manual sweeps stop descending into sibling worktrees.

**Preserve, do not redesign.** Exit semantics (0 clean / 2 issues), the summary output format, and config/ignore loading all keep the installed copy's behaviour. This subphase changes *what gets linted*, never *how results are reported*.

**Acceptance criteria**
- `diff libs/prompting/claude/hooks/smart-lint.sh ~/.claude/hooks/smart-lint.sh` produces **empty output** and exit 0 — the two copies are byte-identical once installed.
- The repo copy contains `find_pruned`, `.claude-hooks-config.sh` / `.claude-hooks-ignore` naming, the `TARGET_FILE` bottom block, and clean-exit-0 semantics — i.e. the drift is genuinely upstreamed, not partially merged.
- `.workflows` appears in `find_pruned`'s prune name list.
- `bash -n` on both copies parses clean, and `shellcheck` (if available) reports no **new** findings versus the installed copy as a baseline — the same differential-baseline rule Phase 1 Step 0 establishes for ruff/flake8 applies here.
- In hook mode, no linter is invoked at all for a non-lintable extension — assert on the *absence* of linter output, not merely on the exit code.
- `git status` shows `libs/prompting/claude/hooks/smart-lint.sh` as the only repo file changed by this subphase.

**No paired test file is required.** `smart-test.sh` only pairs `.py` files (its `require_tests` logic keys off the extension), and this is a bash script, so the hard block that governs 2.1/3.1 does not apply here. Verification is 5.2's invocation matrix.

**Test approach — oracle: `equivalence check`.** CLI-mode behaviour must remain equivalent to the installed copy's pre-change behaviour except for the `.workflows` prune addition; the two file copies must be byte-identical. Capture the pre-change installed copy (e.g. `cp ~/.claude/hooks/smart-lint.sh` into the run dir) as the comparison baseline **before** step 1 overwrites anything.

---

#### 5.2: Verify hook-mode scoping and CLI-mode preservation

**File scope** — no source edits; this subphase produces evidence.

**Work.** Run the four invocations below by hand and paste the output into the exit report. Each targets one behaviour from 5.1; together they cover both modes and both directions (scoped where it should be, unscoped where it must stay).

| # | Invocation | Expected |
|---|---|---|
| a | Bare path argument to a **known-dirty pre-existing `.py`** file (e.g. one of the 11 baseline ruff offenders in `libs/python/anki-tools/anki_tools/`) | Output confined to **that file only** — no other path named anywhere — and **exit 2** |
| b | Bare path argument to a `.md` file | Immediate **exit 0**, one short line, and **no linter output whatsoever** |
| c | Hook-style JSON piped on stdin with a `.py` `file_path` (`{"tool_input":{"file_path":"…"}}`) | Identical behaviour to (a) — proves the `jq` bottom block and the CLI path argument reach the same code path |
| d | No arguments, in a tty | Repo-wide run that lists **no `.workflows/` paths at all** |

**Acceptance criteria**
- All four rows behave as tabulated, with output pasted into the exit report.
- (a) and (c) produce equivalent output modulo the invocation line — the two entry points must not diverge.
- (d) confirms CLI mode is still genuinely repo-wide: it must still report findings from the pre-existing offenders outside this run's file scope, proving the `.workflows` prune did not over-prune into a no-op.
- **Regression check on the run itself:** after 5.1 is installed, a Write to a markdown file no longer reformats unrelated files. Verify by capturing `git status --porcelain` before and after such a write — they must match. This is the observable that motivated the phase, so it is the one that closes it.
- No sibling worktree under `.workflows/` is modified by any of the four invocations.

**Test approach — oracle: `equivalence check`.** Hook mode is compared against the specified per-extension matrix; CLI mode against the pre-change baseline captured in 5.1.

## Risks and settled decisions

### Risks

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R1 (note, **not** a blocker) | `poetry.lock` is `lock-version = "2.1"`, generated by Poetry 2.1.3. The PATH Poetry is 1.8.2 — but that is **not the tool the repo uses**. | `py-install` sources `.venv` and `pip install poetry`; `.venv` has **poetry 2.4.1 / poetry-core 2.4.0`. The plan gate ran the real operation on a throwaway copy: adding `anki = "24.06.3"` and running `.venv/bin/poetry lock` succeeds, exit 0 | Use `.venv/bin/poetry`. Do **not** stop the run over the lock version. (Earlier drafts of this plan called this a blocker; that was wrong.) |
| R2 | The `anki` dependency is undeclared, so `.venv/bin/python -c "import anki"` raises `ModuleNotFoundError`. `get_deck_info.py` only runs by accident under the global pyenv interpreter. | Verified at plan review. *(Note: the venv itself is no longer bare — `init-workspace` has run and it now holds ~45 packages including poetry 2.4.1 and an editable `anki-tools` install. The missing `anki` is the real gap.)* | Fixed by 1.1 declaring the dep. Until then, do not assume `poetry run` can import `anki`. |
| R3 | Anki must not be running when the collection is opened, or the open fails/contends on the lock. | The profile's `-wal` sidecar was present during planning and gone by plan review, i.e. Anki was opened and closed in between | Preserve `get_deck_info.py`'s "Make sure Anki is not running" guidance, raised via `anki.errors.DBError`; 4.2 is dry-run only. |
| R4 | **`~/.claude/hooks/smart-test.sh` hard-blocks** (prints "Missing required test file", exit 2) on the first write of a non-test `.py` with no matching test file. | Fired during planning; hook source confirmed at plan review, including that it searches `<dir>/../tests/test_<base>.py` and exempts `__init__.py` | Every new module is paired with its test file **in the same subphase** — 2.1 for `due_plan.py`, **3.1** for `rebalance_due.py`. 4.1 extends, never creates. |
| R5 | `set_due_date` behaviour is verified for `due` and `ivl` but **not** for FSRS memory state (`card.memory_state`), which exists in 24.06.3. | `anki/cards.py:48` declares `memory_state: FSRSMemoryState \| None`; the plan gate confirmed it is `None` on non-FSRS review cards, so a naive assertion proves little | 4.1 asserts it is unchanged and reports honestly whether the FSRS path was actually exercised. If it is not preserved, stop and raise it. |
| R6 | No Python package in this monorepo has **any** tests, and there is no `py-test` script in `libs/bash/build-tools`. This change introduces the first Python test infrastructure. | repo-wide search for `test_*.py`/`conftest.py` found only Go tests | Kept contained: pytest config in `pyproject.toml`, a local `"test"` script in this package's `package.json`. See D8. |
| R7 | **The lint gate is much stricter than "almost nothing", and it floats.** `py-lint` does `pip install -q ruff` **unpinned** → currently **ruff 0.16.2**, whose default set is **413 rules** — bugbear, `BLE001`, `EXE002`, `I001` isort, a bandit subset — not the E4/E7/E9/F subset an earlier draft of this plan claimed. A ruff upgrade can therefore introduce findings with no code change. Separately, the `PostToolUse` hook enforces a *different* toolchain (black + flake8, E501 at 88). | `ruff check --show-settings` (no config file anywhere); hook output | New code must satisfy both toolchains; format with black defaults. Because the rule set floats, the gate is **differential against a captured baseline** (1.1 Step 0, 4.2), never an absolute zero. Phase 2's unit tests remain the real correctness gate — but do not treat lint as toothless. |
| R8 | **The test hook runs a different pytest than `poetry run` does.** `smart-test.sh` resolves `pytest` via `command -v`, hitting `/home/icarus64/.pyenv/shims/pytest` (**pytest 7.4.3**, global pyenv), not the package `.venv` where 1.1 installs the dev dependency. Different version, different `sys.path`. | Plan gate | Not fatal — the global interpreter is where `anki` actually lives today. But if a hook-time run fails while `.venv/bin/poetry run pytest` is green, **that mismatch is the cause**; do not chase it as a code defect. |

### Settled decisions (all closed — do not re-open)

Every decision point this plan raised has been answered by the user. They are recorded here as constraints, and the subphases above already encode them. The identifiers are kept so the review history stays traceable.

| # | Decision | Settled as | Encoded in |
|---|---|---|---|
| **D1** | Card scope | **Review-queue only** — `queue == 2 and type == 2 and odid == 0`. New, learning, relearning, suspended, buried and filtered-deck cards are excluded. | 3.1 |
| **D2** | Window start | **`--start-offset 1` (tomorrow).** Cards due today or overdue are **never** touched. **No exception:** even the reverse pass never places a card on today or earlier. | 2.1, 2.3, 3.3 |
| **D3** | Unsatisfiable `--max` | **Default: fail.** Cards move one direction only (earlier); if `--max` cannot be met inside the window the run **exits non-zero with nothing written** — no partial writes. **`--set-earlier` (default false)** opts into the mirror: run the earlier pass first, then, if excess remains, sweep from the front pushing cards **later** one day at a time, extending past the last day as needed, so the run succeeds. The user described it as *"reverse the process"*. | 2.3, 2.5, 3.3 |
| **D4** | Interval semantics | **Non-bang `set_due_date(cids, "N")`** — probe-confirmed to leave `ivl` untouched. | 3.2 |
| **D5a** | Max-pass move order | **Largest `ivl` first**, now *subordinate* to the untouched-first preference in D6.3 and used only as its tiebreaker. | 2.1, 2.2, 2.3 |
| **D5b** | Min-pass move order | **Smallest `ivl` first**, likewise subordinate to D6.3 as a tiebreaker. | 2.1, 2.4 |
| **D6.1** | Shift cap | **`--max-shift`, default `14` days** — the plan's proposal, since the user set no number; see 3.3 for the reasoning and `--max-shift none` to disable. Caps how far a card may be pulled **earlier**, measured cumulatively from its original day. **Days that cannot reach `--min` under the cap stay under min** and are reported. | 2.1 (`may_move_to`), 2.4, 2.5 (`short_days`) |
| **D6.2** | Move granularity | **Moves never skip days.** Excess from an over-max day goes to **exactly one day earlier**, even when the receiving day is already in range and the arrival pushes it over; the cascade handles the receiver in turn. **No searching ahead for a day with free capacity.** | 2.2, 2.3, 2.4 |
| **D6.3** | Already-moved cards | **Stay put as a PREFERENCE, not an invariant.** Pulls prefer untouched cards (the user's 22-card day with 6 arrivals pulls from the 16 untouched). Max/min constraints **override** the preference: after 17 cards move from day 10 to day 9, one of those may legitimately cascade on to day 8. | 2.1 (both move orders), 2.2, 2.3, 2.4 |
| **D7** | Write safety | **Backup (`.colpkg`) + plan summary + `y/N` confirm** before writing; `--yes` skips the prompt. | 3.2, 3.3 |
| **D8** | Test infrastructure | **Contained pytest in the package** — dev dependency plus `[tool.pytest.ini_options]` in `pyproject.toml` and a local `test` script. No shared `py-test` script. | 1.1 |
| **D9** | `anki` pin | **Exact `anki = "24.06.3"`** (the lock normalizes it to `24.6.3`; that is correct, not a bug). | 1.1 |

Also settled earlier in the gate, and equally closed:

- **Pre-existing monorepo lint debt is out of scope for this run.** The lint gate is differential against a captured baseline, not an absolute zero — 11 pre-existing ruff findings remain and `ruff check .` exiting non-zero is expected, not a failure. See 1.1 Step 0 and 4.2.
- The two collisions between that gate and this plan's own conventions are resolved **in code, not suppressed**: `BLE001` by catching `anki.errors.DBError` / `AnkiException` instead of `except Exception`, and `EXE002` by giving `rebalance_due.py` a `#!/usr/bin/env python3` shebang. No `# noqa` in the new files.

### Consequences the user should keep in view

These are not open questions — they are the settled behaviour, stated plainly so nobody is surprised by the first dry-run.

1. **`--min` compacts the future queue toward today; `--max-shift 14` is what bounds it.** On any deck spread thinner than `--min` per day, the min pass pulls the whole queue forward: 100 cards at 2/day over 50 days with `--min 8` collapses to roughly 12 days of 8. The default cap stops that at two weeks per card, at the cost of leaving some days under `--min`. If the first dry-run shows more shortfall than wanted, raise `--max-shift`; if it shows more compaction than wanted, lower it.
2. **The default mode can fail outright**, by design (D3). A deck too dense or too back-loaded for `--max` within the window exits non-zero and writes nothing until `--set-earlier` is passed.

   **Expect this on the first real invocation.** The plan's own guess at the deck's shape — `[0, 40, 2, 0, 25, 1]`, used as 2.5's flagship criterion — **fails by design** in default mode: the max pass leaves 24 cards on the first day against `--max 16`, which raises rather than writes. If `programming::coding` is back-loaded anything like that, `--min 8 --max 16` alone will refuse and `--set-earlier` will be needed. Nothing is wrong when that happens; it is D3 doing its job. The 4.2 dry-run is what settles which case the real deck is in, before anything is written.
3. **The tool is idempotent and safe to re-run**, so a weekly routine is viable; a second run over a conforming distribution produces no moves.

### Assumptions I could not verify

- **The exact card counts and due-date distribution in the real `programming::coding` deck** — the collection was deliberately not opened during planning. Everything about the deck's shape is inferred from the request, which is why the 4.2 dry-run is a required deliverable rather than a nicety: it is what turns points 1 and 2 above from predictions into facts.
- **FSRS memory-state preservation across `set_due_date`** — see R5; asserted in 4.1 rather than assumed here.
- **Whether `col.decks.id_for_name` case-insensitivity could match an unintended deck** — its sibling `by_name` is documented as *"Get deck with NAME, ignoring case"*. 3.1 mitigates by echoing the resolved deck names before doing anything.

## Skill mapping

| Part | Skill / agent |
|---|---|
| Phase 1 dependency install inside the lane worktree | `init-workspace` |
| Phases 1–4 implementation | `builder` (single lane, `l1`), dispatching `coder` per packet |
| Test authoring for every `new contract tests` oracle | `contract-tester`, working from the detail blocks above without reading the implementation |
| Post-build verification | `review-code` |
| Documentation (explicitly out of the build's scope) | `document-local` — `README.md` / `/docs` for `libs/python/anki-tools` |
| Ship | `review-pr`, then `push-pr` |
