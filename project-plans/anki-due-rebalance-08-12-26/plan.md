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
  - [x] 5.1: Scope hook-mode linting to the triggering file
  - [x] 5.2: Verify hook-mode scoping and CLI-mode preservation (after: 5.1)
- [ ] Phase 6: Early backup, feasibility precheck, range windowing, and sliding mode
  - [ ] 6.1: Shared core — early backup, feasibility precheck, cosmetic fixes
  - [ ] 6.2: Range windowing and containment in the core (after: 6.1)
  - [ ] 6.3: Sliding target line in the shared core (after: 6.2)
  - [ ] 6.4: Cap-aware feasibility — the reachability check (after: 6.3)
  - [ ] 6.5: CLI surfaces — `--range`, `--sliding`, and the `anki-due-stats` command (after: 6.4)
  - [ ] 6.6: Verification, including the default-mode regression guarantee (after: 6.5)

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
- **Phase 6 additions to the existing package** — `anki_tools/due_stats.py` (new read-only stats command) plus in-place changes to `due_plan.py` and `rebalance_due.py`. Phase 6 adds a cap-aware feasibility precheck, moves the backup ahead of planning, and introduces an optional `--range LO-HI` day-offset window and an optional `--sliding` target line. **`due_plan.py` is not forked**: sliding is a parameter on the existing passes, not a second implementation.
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

Every signature, stated once and binding on 2.2–2.5 and both test files.

> **[SUPERSEDED by 6.3]** — the three `apply_*_pass` signatures below take **scalar** `max_per_day` / `min_per_day`. Phase 6 replaces every scalar bound with a per-day `DayTargets` mapping and adds a fourth pass (`apply_shape_pass`). Flat-mode *behaviour* is unchanged (a constant mapping reproduces the scalar exactly); only the parameter shape moves. `RunState`, `CardDue`, `may_move_to`, `move_card` and both selection orders are **unaffected**. See 6.3 for the superseding forms, and 6.2 for the `max_end_day` field `RunState` gains.

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

Sequence, in exactly this order.

> **[SUPERSEDED by 6.3]** — this sequence is the **flat-mode** form and remains correct for it. Phase 6 adds: a hard feasibility precheck ahead of everything (6.1), an explicit `end_day` window with containment (6.2), and, in sliding mode, `apply_shape_pass` between the over-max resolution and the min pass, with the min pass fed `T(d)` instead of a scalar floor (6.3 pins the full five-step sliding sequence). The `RebalanceResult` also gains `over_target_days`. **Step ordering for flat mode does not change.**

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
- **Order of operations is a safety property, not a detail.** ~~`plan_rebalance` runs to completion *before* the backup is taken~~ **[SUPERSEDED by 6.1]** — the backup now runs **before** planning, and the feasibility precheck before that: `open -> collect -> precheck -> backup -> plan -> confirm -> apply`. `plan_rebalance` still completes before any `set_due_date` call. An `InfeasibleRebalance` (2.5) therefore aborts with the collection untouched and no backup churn — the settled D3 guarantee of "exits non-zero with nothing written" depends on this ordering.
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

---

### Phase 6: Early backup, feasibility precheck, range windowing, and sliding mode

**Origin.** User feedback after the first real apply, which succeeded (1943 moves, idempotent, in-band). Three requirements plus two cosmetic defects already logged in the code and PR reviews. Rides PR #12 on the same branch.

**Structural rule for the whole phase — one core, several surfaces.** The user asked to *"keep the current version as the 'simple' version and make either a complex version or other tools/sh commands that do some of these asks"*. That is honoured by **adding surfaces, never by forking the algorithm**:

- `due_plan.py` remains the **single shared core**. There is no "complex copy" of it, and no sliding-specific duplicate of any pass. Every new capability is a parameter on the existing machinery.
- The existing command keeps its current behaviour by default (see the regression rule below).
- New capability reaches the user through a flag on the existing command and one new read-only sibling command.

**What "unchanged default behaviour" means — scoped precisely, because two requirements collide.** The requirement is *scheduling semantics*: **for identical inputs, the set of `(card_id → new_day)` moves and the resulting collection state must be byte-for-byte identical pre- and post-phase.** It is deliberately **not** literal stdout equality, because two of this phase's own required fixes intentionally change printed text (the mislabeled day-offset line, and the histogram signature losing its dead parameter), and the early backup adds one reporting line. 6.5's regression check therefore asserts on **moves and final card state**, not on captured stdout. Stating this here rather than discovering it at verification time.

---

#### 6.1: Shared core — early backup, feasibility precheck, cosmetic fixes

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py` (the precheck — pure, no `anki` import)
- `libs/python/anki-tools/anki_tools/rebalance_due.py` (backup ordering, cosmetics)
- `libs/python/anki-tools/tests/test_due_plan.py`
- `libs/python/anki-tools/tests/test_rebalance_due.py`

**Work — (a) FIRST ACTION OF THE PHASE: capture the pre-phase behavioural baseline.** Before editing `due_plan.py` or `rebalance_due.py` at all — the pre-phase behaviour is unrecoverable once they change, except from git.

1. Copy the current `anki_tools/due_plan.py` and `anki_tools/rebalance_due.py` to `<parent-worktree>/.artifacts/pre-phase6/`. (Gitignored scratch, per the run-artifacts rule — never a committed plan record.) `git show HEAD:<path>` is an acceptable equivalent source.
2. Run the **three pinned fixtures** through that pre-phase copy and write each `{card_id: new_day}` mapping as JSON, keys sorted so the files diff cleanly, to `<parent-worktree>/.artifacts/pre-phase6/moves-<fixture>.json`:
   - **F1 — feasible flat:** needs only the max and min passes; no reverse pass, no cap blocking.
   - **F2 — reverse pass:** back-loaded, requires `--set-earlier`, exercises horizon extension.
   - **F3 — cap-blocked:** `--max-shift 14` blocks fills, producing a non-empty `short_days`.

   All three in **default mode** — no `--range`, no `--sliding` — since that is the behaviour the regression guarantee covers.
3. 6.6 compares the post-phase run of the same three fixtures against these files.

This is step (a) because it must precede every other edit in the phase, including the backup reordering below.

**Work — (b) back up before planning, after the precheck. The exact order is pinned here because two settled requirements meet at this point.**

```
open collection -> collect in-scope cards -> PRECHECK -> (pass) BACKUP -> plan -> confirm -> apply
                                                \-> (fail) exit non-zero: nothing written, nothing backed up
```

The user's requirement was *"backup before anything"* (meaning before planning and applying, in **every mode including `--dry-run`** — it currently runs only on the apply path, and at ~9 MB it is cheap insurance). The settled DP-B ruling then places the feasibility precheck **before** the backup. These do not conflict, and the reason is worth stating so nobody "fixes" it later:

**A failed precheck is read-only arithmetic.** It reads card due-dates already in memory, writes nothing, and modifies nothing. There is no state to recover, so a backup would be pure cost — ~9 MB and the wall time — for a run that provably did not touch the collection. The backup's actual value is as a **pre-apply snapshot to roll back to**, which requires only that it precede the first write. It does.

**This supersedes 3.2's ordering statement.** Subphase 3.2 (already built) says *"`plan_rebalance` runs to completion before the backup is taken"*. That is now wrong: the backup moves **ahead** of planning. 3.2's underlying guarantee — that an `InfeasibleRebalance` aborts with the collection untouched — still holds, and is unaffected by where the backup sits. Update 3.2's wording as part of this subphase so the plan does not contradict itself.

**Two distinct failure modes, which differ only in whether a backup exists:**

| failure | when | backup taken? | collection |
|---|---|---|---|
| **Precheck failure** (DP-B bounds, prefix/Hall) | before backup | **no** | untouched |
| **`InfeasibleRebalance`** from `plan_rebalance` | after backup, during planning | **yes** | untouched |

Both exit non-zero and write nothing. Tests must assert the *backup* difference, not just the exit code — it is the only observable that distinguishes them.

This changes no scheduling semantics, so it does not violate the default-behaviour rule above — the simple version gets the safety fix too, which is the point.

**Work — (c) the feasibility precheck.** A **pure function in the core**, called by every surface before planning:

```python
@dataclass(frozen=True)
class FeasibilityReport:
    total: int                                    # in-scope scheduled cards
    first_day: int                                # == start_day
    last_day: int                                 # == end_day (max origin among in-scope cards)
    horizon_days: int                             # D = last_day - first_day + 1
    avg_per_day: float                            # total / D
    mode: str                                     # "flat" | "sliding"
    capacity: int                                 # sum of per-day targets across the window
    # ---- HARD gate (DP-B). Constant max/min ONLY; never T(d). ----
    feasible: bool                                # False => exit non-zero before backup and planning
    violations: list[str]                         # human-readable, each printing its arithmetic
    binding_prefix: tuple[int, int, int] | None   # (day, cards_due_by_then, capacity_by_then)
    suggested_min: int | None
    suggested_max: int | None

    # ---- INFORMATIONAL shape analysis (sliding only). NEVER gates. ----
    shape_reachable: bool | None                  # None in flat mode
    predicted_over_target_days: list[int]         # days expected to sit above T(d)
    shape_gap: int                                # total cards above T(d) that cannot migrate
    min_feasible_max_shift: int | None            # from the 6.4 bisection; what WOULD reach the shape

# ---- ONE shared window kernel. The `capacity` argument is what distinguishes the two legs. ----
def window_violations(
    counts: Mapping[int, int],
    start_day: int,
    end_day: int,
    capacity: DayTargets,          # HARD leg passes constant_targets(max); SHAPE leg passes T
    max_shift: int | None,
) -> list[tuple[int, int, int, int]]:      # (a, b, confined, capacity_in_window)
    ...

# ---- HARD gate (DP-B). Capacity is ALWAYS constant max_per_day. Never T(d). ----
def check_hard_feasibility(
    cards: Sequence[CardDue],
    start_day: int,
    end_day: int | None,           # None = derive from cards; set in --range mode
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None,
    *,
    set_earlier: bool = False,
) -> HardFeasibility: ...

# ---- INFORMATIONAL shape analysis. Sliding only. Capacity is T(d). NEVER gates. ----
def analyze_shape(
    cards: Sequence[CardDue],
    start_day: int,
    end_day: int,
    target: DayTargets,            # the T(d) line from 6.3
    max_shift: int | None,
) -> ShapeAnalysis: ...

# ---- Composition. Returns both blocks; only the hard block can stop a run. ----
def check_feasibility(
    cards: Sequence[CardDue],
    start_day: int,
    end_day: int | None,
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None,
    *,
    sliding: bool = False,
    set_earlier: bool = False,
) -> FeasibilityReport: ...
```

**`max_shift` is a required parameter, not an optional extra.** Both legs need it: the hard leg because a cap-blocked day genuinely stays over `max_per_day` and so genuinely raises, and the shape leg because `min_feasible_max_shift` is a bisection over it. A `FeasibilityReport` cannot be computed without it, and there is no call path that omits it.

`check_feasibility` calls `check_hard_feasibility` always, and `analyze_shape` only when `sliding` is true (otherwise the informational fields are `None`/empty). **`analyze_shape`'s result never influences `feasible`.**

The checks, in order:

1. **Global upper bound.** `total <= D × max_per_day`, in **BOTH** modes. In flat mode this is exactly the user's `avg <= max`.

   **The hard gate NEVER uses `T(d)`, in any mode.** This is the one rule that keeps DP-B and DP-F from contradicting each other, and it is easy to get wrong. `sum(T(d))` is always `<= D × max_per_day` (the line descends from `max`), so using it as the DP-B threshold would hard-fail precisely the decks DP-F option 1 — the recommended default — exists to serve. Concretely, on the real block: 1360 cards against an area under `T` of 826 would hard-fail, when the settled answer is that such a run **proceeds best-effort and reports `over_target_days`**. The user's own deck is plausibly in this category, so this is not a corner case.

   `T(d)`-based analysis is **informational only** — it predicts `over_target_days`, sizes the shape gap, and drives the minimum-feasible-`--max-shift` figure. It is reported by `anki-due-stats` and in the run summary. **It never gates a run.**
2. **Global lower bound** (only when `min_per_day` is given). `total >= D × min_per_day` in flat mode — the user's `avg >= min`. **Settled (DP-B): this is a HARD failure, with no escape flag** — see the settled table. It can reject runs that succeed today, and that is the intended strict behaviour.
3. **Window (Hall) condition — the one that actually binds.** `window_violations(counts, start_day, end_day, capacity=constant_targets(start_day, end_day, max_per_day), max_shift)` must return empty.

   **Capacity here is `max_per_day`, exactly as in checks 1 and 2 — never `T(d)`.** "The hard gate never uses `T(d)`" holds for **all three checks**, not just the global one. This leg is where it is easiest to lose, because 6.4 states the same window algorithm in terms of a generic `target`, and it is tempting to feed it the sliding line.

   **Counterexample, verified.** Window `1..10`, `min=8 max=16 --sliding`, with **46 cards** of origin `<= 3`. Hard capacity for that prefix is `3 × 16 = 48`, so the run is feasible and the planner will not raise; `sum(T(1..3)) = 16 + 15 + 14 = 45`, so a `T`-fed hard leg would reject it. Anything in **46-48 cards** reproduces the DP-B/DP-F contradiction that B25's first half already removed from the global leg.

   **This is structural, not a corner case.** Exhaustive check over every window length `D` in `[2, 60)` and every `(min, max)` pair with `0 <= min < max <= 24`: **`sum(T(d))` over a prefix NEVER exceeds `max_per_day × len`** — the `T`-based condition is always at least as strict as the hard one, for every parameter combination. So feeding `T` to the hard leg can only ever manufacture false failures; it can never catch a real one the hard leg misses.

   **Why this is not optional.** Cards move **earlier only**, so a card with origin `o` can land anywhere in `[start_day, o]` — which makes *prefixes* the only sets that can be over-subscribed. Verified against this plan's own known-infeasible distribution `[0, 40, 2, 0, 25, 1]` with `max=16` (2.5's flagship criterion, which raises `InfeasibleRebalance`): the **global average check passes** (`avg = 11.33 <= 16`) while the prefix check catches it at day 2 — **40 cards due by then against 32 slots**. An average-only precheck would clear a distribution the planner then refuses, which is precisely the failure this phase exists to prevent.

   This condition is **necessary and sufficient** for earlier-only placement with no shift cap. With a finite `--max-shift` each card also gains a lower bound (`origin - max_shift`), the intervals stop being nested, and the condition remains **necessary but no longer sufficient** — so the precheck is a fast, honest screen and `plan_rebalance` remains the authority. Say so in the code comment; do not oversell it.

4. **`--set-earlier` interaction.** When `set_earlier` is true, horizon extension can cure any *upper-bound* or *prefix* violation, because the window is no longer fixed. Such violations are **downgraded to warnings whose text says exactly that** — never silently passed. The lower-bound violation is unaffected by `set_earlier`.

**Only `feasible` can stop a run.** `shape_reachable is False` is printed, never fatal — unless `--strict-sliding` is passed (6.3).

**Failure behaviour.** On `feasible is False`, the calling surface exits non-zero **before any move planning**, printing the arithmetic (total, horizon days, avg/day, the violated bound and its numbers, and the binding prefix day when that is what failed) **and a suggested `--min`/`--max` that would be feasible**:
- `suggested_max` (flat) = `max(ceil(total / D), max over k of ceil(count(origin <= k) / (k - start_day + 1)))` — the exact smallest flat `max` satisfying both the global and every prefix bound. For `[0,40,2,0,25,1]` this is **20**, verified.
- `suggested_min` (flat) = `floor(total / D)`.
- Sliding suggestions: hold one endpoint and scan the other upward from its current value to the first value satisfying every condition. `D` is small, so a linear scan is exact and adequate; do not derive a closed form that ignores the prefix bounds. (The closed-form global-only answer for `[0,40,2,0,25,1]` holding `min=8` is `max=15`, which the prefix condition then rejects — a worked example of why the scan is required.)

**Work — (d) the two cosmetic defects**, both already logged in review:
- The summary line labels an **absolute day number** as a "day offset" (prints e.g. `2172` where the reader expects `363`). Fix by printing the offset from today (`absolute_day - today`), keeping the "offset" wording. While there, check whether the *"was extended"* message fires when the final `end_day` merely **equals** the pre-existing maximum; it must fire only on a strict increase.
- `render_histogram` carries a dead `min_per_day` parameter. Remove it. 6.3 changes this signature again (the histogram needs the target line, not scalar bounds), so make the removal consistent with that direction rather than churning it twice.

**Acceptance criteria**
- A `--dry-run` against a synthetic collection leaves a **fresh `.colpkg`** in the backup directory, and the collection itself is unmodified.
- **Ordering asserted, both failure modes:**
  - a **precheck failure** exits non-zero with **no backup created** and no card's `due` changed;
  - an **`InfeasibleRebalance` raised by `plan_rebalance`** exits non-zero with a **backup present** and no card's `due` changed.
  Assert the backup-directory contents in both cases — the exit code alone does not distinguish them.
- The `--min`-omitted case runs **no lower-bound check at all** (a max-only run cannot fail on `avg < min`).
- `check_feasibility` is pure: importable and fully exercised with no `anki` import and no collection.
- On `[0,40,2,0,25,1]`, `start_day=1`, flat `max=16`: `feasible is False`, `binding_prefix == (2, 40, 32)`, `avg_per_day == pytest.approx(11.33, abs=0.01)`, and `suggested_max == 20`. **Also assert the global average check alone would have passed** — this is the test that pins why the prefix condition is present.
- The same input with `set_earlier=True` reports `feasible is True` with a warning naming horizon extension as the cure.
- **Cap-unreachable but max-feasible deck PASSES the precheck (the DP-B/DP-F boundary).** The real-block distribution — days 244-328 at 16/day, `min=8 max=16 max_shift=14 --sliding` — has `total <= D × max_per_day` and so returns **`feasible is True`**, while reporting `shape_reachable is False`, a non-empty `predicted_over_target_days`, and `min_feasible_max_shift == 48`. **Assert that the run is NOT blocked.** A `feasible is False` here would mean the hard gate has been wired to `sum(T(d))` — the exact defect this criterion exists to catch.
- A feasible flat distribution returns `feasible is True` with an empty `violations` list.
- The summary prints an offset (e.g. `363`), never a raw absolute day (e.g. `2172`); a run whose `end_day` equals the pre-existing maximum does **not** claim the horizon was extended.
- `render_histogram` no longer accepts `min_per_day`.

**Test approach — oracle: `new contract tests`** for `check_feasibility` (pure, table-driven); **`equivalence check`** for the backup reordering, which must not alter any computed move.

---

#### 6.2: Range windowing and containment in the core

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

*(The adapter-side card filter and `--range` parsing live in 6.5; this subphase pins the core contract they depend on.)*

**The user's request, verbatim.** *"It should also take in a date range even if its just number like 8-30 so it would be from 8 days away to 30 days away (like how anki sets due dates) that way if i only wanted to fix a certain part of the deck and not the full thing."*

**The slice is the whole universe for the run.** With a range in effect, `[LO, HI]` is not a filter layered over a full-deck plan — it *is* the plan's entire world. Cards outside the range are untouched, and they are also excluded from every count, every source and every sink. A card due on day 40 is not a candidate to fill day 25 under `--range 8-30`; it does not exist for that run. This is the single idea the rest of the subphase implements.

**Day offsets, not absolute days — the conversion happens at the CLI boundary.** `LO` and `HI` are **offsets from today**, matching Anki's own set-due-date syntax. The core continues to work in absolute day numbers throughout: 6.5 converts `start_day = today + LO` and `end_day = today + HI` before calling in. This split is stated explicitly because conflating the two is exactly the defect 6.1 fixes in the summary line; do not repeat it here.

**`D2` holds structurally, not by convention.** `LO >= 1` is enforced at parse time, so `start_day >= today + 1` and no card can ever be placed on today or earlier — in either direction, in any mode. The range cannot be used to reach into the past.

**Core contract changes.**

```python
def plan_rebalance(
    cards, start_day, min_per_day, max_per_day,
    max_shift=14, set_earlier=False, sliding=False,
    end_day=None,            # NEW: explicit window ceiling (absolute day). None = derive from cards.
) -> RebalanceResult
```

`RunState` gains one field:

```python
max_end_day: int | None      # containment ceiling; None = unbounded (horizon may extend)
```

- **`end_day is None`** (no range) → derived as the maximum `day` among the input cards, exactly as today, and `max_end_day = None`. **This is the default path and its behaviour is unchanged.**
- **`end_day` given** (range mode) → `state.end_day = end_day` and `state.max_end_day = end_day`.

**Containment, both directions.**

- **Downward** is already structural: `may_move_to` refuses any `target_day < state.start_day`, and `start_day == LO`. Point 8 of the requirement falls out of this — a card whose `--max-shift` budget would allow an earlier landing than `LO` is **still clamped to `LO`**, because the window floor is checked independently of and takes precedence over the shift cap. No new code; assert it.
- **Upward** needs a new gate, kept separate from `may_move_to` so the N21 resolution stands (that `may_move_to` is the *earlier-direction* gate and the reverse pass does not consult it):

```python
def may_move_later_to(target_day: int, state: RunState) -> bool:
    """Later-direction gate. False when the containment ceiling would be crossed."""
    return state.max_end_day is None or target_day <= state.max_end_day
```

**The reverse pass consults `may_move_later_to` before every placement** (and still never consults `may_move_to`). When the gate refuses, the pass **leaves the excess where it is and stops advancing** — it does not raise. The day then remains above the hard cap, and 2.5's existing `over_max` check produces `InfeasibleRebalance` with the offending days. **No new raise path is introduced**; range overflow reuses the one that already exists, which is what keeps the infeasibility story single.

**No horizon extension in range mode.** `move_card` may still create a new day and raise `state.end_day`, but only when `max_end_day is None`. Under a range the ceiling is fixed, so `state.end_day` never moves and every downstream consumer — the sliding target line, the histogram, the post-conditions — sees a stable window.

**`build_buckets` bounds check.** It already raises `ValueError` for `day < start_day`; it must now also raise for `day > end_day` when the window is explicitly bounded. Callers are responsible for having sliced first (6.5 does), so this fires only on a caller bug — which is precisely why it should be loud.

**Interactions, stated so none is inferred.**
- **`--sliding`** ramps `T(d)` from `max` at `LO` to `min` at `HI`, since `build_target_line` already takes `start_day`/`end_day`. The slide is over the *slice*, not the deck.
- **Feasibility (6.1) and the cap-aware Hall check (6.4)** are computed **on the slice**: the card set, the horizon `D = HI - LO + 1`, the averages, the prefix windows and the capacity all come from the range alone.
- **`--max-shift`** is unchanged — still measured per-card from `origin_by_id`, additionally clamped by the `LO` floor as described above.
- **`--set-earlier`** still runs the reverse pass, but its spill is capped at `HI` rather than extending indefinitely.

**Post-conditions in range mode** (additions to 2.5's list):
- No card lands below `LO` — the existing floor post-condition, with `start_day == LO`.
- **No card lands above `HI`.**
- `state.end_day == HI` on exit; the horizon never moved.
- Cards outside `[LO, HI]` are absent from `moves` entirely, having never entered the run.

**Acceptance criteria**
- `end_day=None` reproduces the pre-range behaviour exactly on every existing 2.x fixture — same move sets, same derived `end_day`. **This is the no-regression anchor for the whole requirement.**
- With `end_day` set, `state.max_end_day == end_day` and `state.end_day == end_day` on exit, even when `set_earlier=True` and the reverse pass runs.
- **Upward containment:** a range-mode distribution whose excess cannot be absorbed by `HI` raises `InfeasibleRebalance` naming the offending days — and **not** some new exception type.
- **Downward containment under a generous cap:** with `max_shift=None` and a range starting at `LO`, no card lands below `LO`.
- **Shift cap clamped by `LO`:** a card with origin `LO + 3` and `max_shift=14` lands no earlier than `LO`, never `LO - 11`.
- `build_buckets` raises `ValueError` for a card above a bounded `end_day`, as it already does below `start_day`.
- A single-day range (`LO == HI`) is legal and degenerate: the window is one day, and 6.3's degenerate target line (`{start_day: max_per_day}`) applies.
- With a range in effect, cards outside it never appear in `moves`, `before`, `after`, `short_days` or `over_target_days`.

**Test approach — oracle: `new contract tests`.**

---

#### 6.3: Sliding target line in the shared core

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

**The user's request, and why a linear line answers it.** The ask, verbatim: *"i know lowering max would fix this some, but i was really wondering if there is a way to clean this up so that it kept days like 300-365 as being 10 max and then 200-300 as 12 max etc. maybe give it a --sliding true var?"* — and earlier, *"smaller card counts the farther away from today, closer to today the closer to max, like a slide."*

The user's mental model is **banded per-region caps**: 300-365 → 10, 200-300 → 12, and so on. The linear per-day target is the **smooth generalization of exactly that**, and their own example bands sit almost on the line: a 16→8 ramp across days 1-365 gives `T(250) = 11` and `T(330) = 9`, against their sketched 12 and 10. **No separate band syntax ships in this phase** — the line covers the ask with one parameter pair instead of a band-list grammar. If explicit bands are ever wanted, they become a different target-line builder feeding the same machinery.

**The flag is `--sliding`** (a `store_true` boolean — `--sliding`, not `--sliding true`), using the user's own term.

**The target line — pinned exactly, because a blind test author must reproduce it.**

```python
def build_target_line(start_day: int, end_day: int, min_per_day: int, max_per_day: int) -> dict[int, int]
```

```
T(d) = floor( max - (max - min) * (d - start_day) / (end_day - start_day) + 0.5 )
```

- **Rounding is `floor(x + 0.5)`, NOT Python's `round()`** (banker's rounding would make `T` depend on parity). Pinned, not incidental.
- Endpoints exact by construction: `T(start_day) == max_per_day`, `T(end_day) == min_per_day`.
- **Degenerate window:** `end_day == start_day` → `{start_day: max_per_day}` (no division).
- Verified: `start_day=1, end_day=6, min=8, max=16` → `{1:16, 2:14, 3:13, 4:11, 5:10, 6:8}`, sum **72**, matching the closed form `D × (max+min)/2 = 72`. Use the **summed rounded values** as authoritative capacity, since rounding can shift it by a few cards.

**Two bounds, not one — this is the central design decision of the phase.** Sliding mode does **not** replace `max_per_day`; it adds a target beneath it:

| bound | value | enforcement |
|---|---|---|
| **Hard cap** | `max_per_day` (constant, as today) | A day above it after the passes → `InfeasibleRebalance`. Unchanged from flat mode. This is the user's actual safety bound. |
| **Soft target** | `T(d)` | The passes aim here. Days left **above** `T(d)` are collected into **`over_target_days`**; days left **below** (non-tail) into `short_days`. Reported, never raised. |

**Why the soft target is not merely a weaker choice.** A day sitting at 16 when `T(d) = 9` is **not harmful** — it is still under the user's absolute maximum; it simply is not the requested shape. Treating `T(d)` as hard would manufacture failures on schedules that are perfectly safe, which is precisely the trap the cap-reachability finding below exposes. Conflating the safety bound with the shape preference is the bug; separating them is the fix.

`--strict-sliding` upgrades `T(d)` to a hard bound for anyone who wants failure instead of a report (see DP-F).

**Flat mode is the same code path with a constant line.** Both modes drive the passes from per-day numbers; **no pass acquires a `sliding` branch**, and `due_plan.py` is never forked. When `--set-earlier` extends the horizon, the target line is **recomputed over the new window** — the one place the line is not fixed at the start.

##### Pass signatures — these SUPERSEDE 2.1's scalar forms

Every pass now takes a **per-day mapping** instead of a scalar bound. Behaviour in flat mode is unchanged (a constant mapping reproduces the scalar exactly); only the parameter shape moves.

```python
DayTargets = Mapping[int, int]          # day -> per-day number, defined for every day in the window

def constant_targets(start_day: int, end_day: int, value: int) -> dict[int, int]: ...

def apply_max_pass(state: RunState, ceiling: DayTargets) -> None: ...
def apply_reverse_max_pass(state: RunState, ceiling: DayTargets) -> None: ...
def apply_min_pass(state: RunState, floor: DayTargets) -> None: ...

# Sliding only. Shapes DOWNWARD toward `target` without ever breaching `hard_ceiling`.
def apply_shape_pass(state: RunState, target: DayTargets, hard_ceiling: DayTargets) -> None: ...
```

Inside the passes, every former `max_per_day` / `min_per_day` comparison becomes `ceiling[d]` / `floor[d]`. Nothing else in 2.2, 2.3 or 2.4 changes.

##### Why sliding needs TWO stages, not a substitution

The tempting shortcut — call `apply_max_pass(state, T)` and be done — **breaks the hard-cap guarantee.** `T(d) <= max_per_day` everywhere, so shedding toward `T` moves strictly *more* cards earlier than shedding toward `max`. Those extra cards cascade down and pile onto `start_day`, which the max pass never sheds from (its loop stops at `start_day + 1`). The sink can therefore end **above `max_per_day`**, raising `InfeasibleRebalance` on a deck that is perfectly feasible under the flat cap. Being greedy about the soft target destroys the hard guarantee.

So the hard result is established **first**, by the unchanged flat-cap pass, and shaping is a strictly-optional refinement layered on top that **may never undo it**:

```
sliding mode, inside plan_rebalance:
  1. apply_max_pass(state, constant_targets(..., max_per_day))     # HARD guarantee, identical to flat
  2. over_max check -> raise InfeasibleRebalance, or reverse pass  # HARD guarantee settled here
  3. apply_shape_pass(state, T, constant_targets(..., max_per_day))# SOFT shaping downward
  4. apply_min_pass(state, T)                                      # SOFT shaping upward
  5. over_target_days = [d for d in window if len(buckets[d]) > T[d]]
     if strict_sliding and over_target_days: raise InfeasibleRebalance
```

Flat mode is steps 1, 2, then `apply_min_pass(state, constant_targets(..., min_per_day))` — step 3 does not run and step 5 yields `None`. **This supersedes 2.5's orchestration sequence**, which knows only the flat form; update its step 4/5 wording accordingly.

##### `apply_shape_pass` — pseudocode

```
for d from state.end_day down to state.start_day + 1:
    while len(state.buckets[d]) > target[d]:
        if len(state.buckets[d - 1]) >= hard_ceiling[d - 1]:
            break          # receiver is AT the hard cap -> refuse this move
        mover = first cid in max_move_order(state.buckets[d], state)
                that satisfies may_move_to(cid, d - 1, state)
        if mover is None:
            break          # shift cap blocks every remaining candidate on this day
        move_card(mover, d, d - 1, state)
```

- **The `break` on a full receiver is a REFUSAL, not a skip.** It stops shaping day `d` and moves the sweep on; it does **not** look at `d - 2`. D6.2 forbids *searching past* an in-range day for capacity, and this does not do that — the target is always exactly `d - 1`.
- **The hard cap cannot be breached**, because every move is gated on `len(buckets[d - 1]) < hard_ceiling[d - 1]`. That gate is also what protects the sink at `start_day`.
- Selection is `max_move_order` (untouched-first, then D5a's largest-`ivl`), and `may_move_to` enforces `--max-shift` and the `start_day` floor — all unchanged.
- Descending sweep, one day at a time, so a card shifted to `d - 1` is reconsidered when the sweep reaches `d - 1`. Every move strictly decreases a card's day, bounded below by `start_day`, so the pass terminates.
- Days still above `target[d]` on exit are exactly `over_target_days`. **The pass never raises.**

All existing machinery is preserved verbatim: one-day cascade, untouched-first selection, D5a/D5b tiebreakers, `--max-shift` via `may_move_to`, and the reverse pass. **Recorded correction:** the reverse pass as built matches the user's intent exactly (forward cascade from day 1, dying when absorbed — verified live at the day 27 = 15 / day 28 = 9 dying edge). **Its semantics are unchanged here**; sliding mode only retargets it at `T(d)`.

**Post-conditions in sliding mode** (replacing 2.5's constant bounds; everything else unchanged):
- **Hard:** every day in `[start_day, end_day]` holds at most `max_per_day`. Violation raises, as today.
- **Soft:** `over_target_days` lists days above `T(d)`; `short_days` lists non-tail days below `T(d)`. Neither is asserted.
- **"Infeasible" in sliding mode** therefore means the same as in flat mode — a day still above the **hard cap** — not a missed target.

**Acceptance criteria**
- `build_target_line(1, 6, 8, 16)` returns exactly `{1:16, 2:14, 3:13, 4:11, 5:10, 6:8}`.
- Endpoints exact and the line monotonically non-increasing across several `(min, max, D)` combinations.
- `end_day == start_day` → `{start_day: max_per_day}`.
- A `.5` case landing on an even integer resolves the `floor(x + 0.5)` way, not `round()`'s.
- A sliding run over a cap-reachable distribution leaves every day at or under `T(d)`, with `over_target_days` empty.
- **A cap-blocked sliding run does NOT raise**: days stay above `T(d)`, appear in `over_target_days`, and remain at or under `max_per_day`.
- **Two-stage necessity, directly tested.** Construct a distribution that is feasible under the flat cap but whose sink would overflow if shedding aimed at `T(d)` from the start. Assert the specified two-stage order leaves every day at or under `max_per_day` and raises nothing — and, as a guard, that a single-stage `apply_max_pass(state, T)` on the same input would drive `start_day` above `max_per_day`. This is the criterion that pins *why* the sequence is what it is.
- **`apply_shape_pass` never breaches the hard ceiling:** after it runs, no day exceeds `hard_ceiling[d]`, including `start_day`, for every fixture in the suite.
- **Refusal, not skip:** when day `d - 1` sits at the hard cap, day `d` is left above `T(d)` and **no card lands on `d - 2`** from that attempt.
- `constant_targets` fed to the three original passes reproduces the pre-phase scalar behaviour move-for-move.
- **Flat mode is bit-identical through the shared path:** driving the passes with a constant line reproduces the pre-phase flat move set exactly.
- `--strict-sliding` turns the same cap-blocked case into an `InfeasibleRebalance` naming the offending days and their targets.

**Test approach — oracle: `new contract tests`.**

---

#### 6.4: Cap-aware feasibility — the reachability check

**File scope**
- `libs/python/anki-tools/anki_tools/due_plan.py`
- `libs/python/anki-tools/tests/test_due_plan.py`

**The finding this exists for.** Verified live on the real deck: after the flat apply, **days 244-328 sit at exactly 16/day** — a dense back-loaded block of original deck mass plus normal max-pass spill (not reverse-pass parking; that cascade died around day 28). Those cards are scheduled 8-11 months out. A sliding target of ~9-11/day across that region requires draining it toward today, but **`--max-shift 14` cannot move a day-300 card to day 50.** An area-under-the-line check would call this feasible; the leash makes it unreachable.

**The exact condition — Hall over contiguous windows.** With a shift cap, a card with origin `o` may land in `[max(start_day, o - max_shift), o]`: a sliding window, not a prefix. The sets that can be over-subscribed are therefore all **contiguous day-ranges**, and the condition is exact, not an approximation:

For every window `[a, b]` with `start_day <= a <= b <= end_day`:

```
confined(a, b)  <=  capacity(a, b)

confined(a, b) = |{ cards whose entire legal landing range lies inside [a,b] }|
               = cards with origin o in [a + max_shift, b]      when a >  start_day
               = cards with origin o <= b                        when a == start_day
               = (empty for a > start_day)                       when max_shift is None
capacity(a, b) = sum(target[d] for d in [a, b])
```

**This kernel is `window_violations` (signature pinned in 6.1). It has exactly TWO callers, and they pass DIFFERENT `capacity` arguments:**

| caller | `capacity` passed | gates a run? |
|---|---|---|
| `check_hard_feasibility` (DP-B hard gate) | **`constant_targets(start_day, end_day, max_per_day)`** | **YES** |
| `analyze_shape` (informational, sliding only) | **the `T(d)` line from 6.3** | **NO — reporting only** |

**`target` in the formula above is that parameter, not `T(d)`.** The algorithm is generic over capacity; the *meaning* comes from the caller. Wiring `T(d)` into the hard caller is the B25 defect and is specifically forbidden — see 6.1 check 3 for the verified counterexample and the proof that it can only manufacture false failures.

- **The uncapped prefix condition of 6.1 is the `a == start_day` slice of this**, and the `max_shift is None` case collapses to exactly that. One condition, not two.
- Implement with prefix sums over both `counts` and `target`: there are exactly **`D(D+1)/2`** windows, at O(1) each. For `D = 365` that is **66,795** — trivial, so there is no reason to approximate. (An earlier draft said "~133k, O(D²)", which double-counted by treating ordered pairs as windows.)
- **Minimum feasible `--max-shift`:** feasibility is monotone in the cap (a larger `max_shift` shrinks every `confined` set), so **bisect** `s` over `[0, D]`, running the `D(D+1)/2` check per probe — about 20 probes for `D = 365`. Report the result.

**Verified against the real block** (days 244-328 at 16/day, `min=8 max=16 horizon=365`, block considered alone):

| `--max-shift` | result |
|---|---|
| 14 (default) | **infeasible** — worst window `[230, 328]`: **1360 cards vs 980 slots, gap 380** |
| 30 | infeasible — worst window `[214, 328]`: 1360 vs 1156, gap 204 |
| 60 | feasible |
| **minimum feasible** | **48 days** |

That 48 is a **lower bound**: it considers the block in isolation, and the rest of the deck can only raise it. The area under `T` across the block is 826 against 1360 cards actually there — the shortfall is structural, not marginal.

**Acceptance criteria**
- Reproduces the table above exactly for the block distribution: infeasible at 14 with worst window `[230, 328]` / `(1360, 980)`, infeasible at 30, feasible at 60, minimum feasible **48**.
- With `max_shift=None`, the check reduces to the 6.1 prefix condition — assert identical results on the `[0,40,2,0,25,1]` case, including `binding_prefix == (2, 40, 32)`.
- Monotonicity: feasibility never flips from true back to false as `max_shift` increases (the property bisection depends on).
- `D(D+1)/2` window evaluations with prefix sums (66,795 at `D = 365`), not a cubic scan: a 365-day window completes well within a normal test run.
- The report names the **worst** window (largest gap), not merely the first violated one.
- **The two callers are distinguishable by test.** On the 6.1 counterexample (window `1..10`, `min=8 max=16 --sliding`, 46 cards of origin `<= 3`): the hard caller returns **no violations** (46 <= 48) while the shape caller returns one (46 > 45). A single shared result for both is the B25 regression.

**Test approach — oracle: `new contract tests`.**

---

#### 6.5: CLI surfaces — `--range`, `--sliding`, and the `anki-due-stats` command

**File scope**
- `libs/python/anki-tools/anki_tools/rebalance_due.py` (the `--range`, `--sliding` / `--strict-sliding` flags; the adapter-side slice in `collect_cards`)
- `libs/python/anki-tools/anki_tools/due_stats.py` (**new**)
- `libs/python/anki-tools/tests/test_due_stats.py` (**new — must be created in THIS subphase**)
- `libs/python/anki-tools/tests/test_rebalance_due.py`
- `libs/python/anki-tools/package.json` (one new `bin` entry)

**`smart-test.sh` pairing applies again.** `due_stats.py` is a new non-test `.py`, so `tests/test_due_stats.py` must land in the same packet or the first write hard-blocks (the rule from 3.1). `package.json` is the 1.1 manifest touchpoint, edited here only to add one `bin` entry.

**Structural decision — sliding is a FLAG, stats is a COMMAND** (DP-A). `--sliding` is a different *target shape* for the same operation: same deck argument, same `--dry-run`/`--yes`/`--max-shift`/`--set-earlier`/`--backup-dir` semantics, same output format. A sibling command would duplicate ten flags and need every future safety flag added twice. Default off, so the simple version is untouched. `anki-due-stats` **is** its own command because it is a genuinely different operation — read-only, no planning, no writes, no prompt — and is exactly the *"other tools/sh commands"* the user asked for.

**`--range LO-HI` — the day-offset window.** Parsed like Anki's set-due-date syntax, on the user's own `8-30` string form:

- **Accepted forms:** `LO-HI` (e.g. `8-30`) and a bare `N` (e.g. `12`), which means `N-N` — a legal, degenerate single-day window.
- **Validation**, each with its own `parser.error(...)` message: both parts integers; `LO >= 1` (so D2 holds structurally — the range can never reach today or the past); `HI >= LO`.
- **Conversion at this boundary:** `start_day = today + LO`, `end_day = today + HI`, passed to `plan_rebalance(..., end_day=…)`. The core works in absolute days; `LO`/`HI` stay offsets everywhere the user sees them (6.2).
- **Mutually exclusive with `--start-offset`**, which sets the window start by itself — supplying both is a usage error, not a silent precedence rule. Use argparse's mutually-exclusive group so `--help` shows it.
- **Adapter-side slice:** `collect_cards` gains the upper bound, admitting a card only when `start_day <= card.due <= end_day`. Out-of-range cards are counted in the skip report under their own reason (`outside --range`) — **not** silently dropped, and not lumped in with the existing "already due or overdue" bucket.
- **No range given** → `end_day=None` and the pre-range behaviour is reproduced exactly.

**`anki-due-stats` accepts `--range` with identical parsing and semantics**, and reports on the slice: the totals, horizon, averages, feasible ranges, the required-vs-cap-achievable profile and the minimum feasible `--max-shift` are all computed over `[LO, HI]` alone. This is what lets the user inspect one region of the deck before deciding whether to touch it.

**Histogram** renders the slice only, printing the offsets as-is — they are already day offsets, so no conversion and no relabelling (this is the same offset-vs-absolute distinction 6.1 fixes in the summary line).

**`--sliding` requires both `--min` and `--max`** (the line needs both endpoints); `parser.error(...)` otherwise. Help text states that it replaces the flat band with a per-day target sliding from `max` at the window start to `min` at the horizon, and that `--max-shift` may prevent the shape from being reached.

**`anki-due-stats DECK [--start-offset N] [--collection PATH] [--min N] [--max N] [--sliding]`** prints, from the same core functions:
- total in-scope scheduled cards, horizon in days, first/last day of the window, average cards/day
- the feasible flat `min`/`max` range, and the feasible sliding range
- **the required vs cap-achievable profile** — per day-range, `T(d)` against what `--max-shift` actually permits, with the worst window and its gap
- **the `--max-shift` value that WOULD make the sliding shape reachable**, from the bisection in 6.4, so the user can consciously weigh interval distortion against shape
- when `--min`/`--max` are supplied, whether that pair is feasible in each mode, with the binding constraint and its arithmetic when not

It opens read-only, writes nothing, takes no backup, and **exits 0 even when the deck is infeasible** — it is a report, not a gate. Register as `"anki-due-stats": "anki_tools/due_stats.py"`, mode 755, shebang-first, with the typed-except convention from 3.1.

**Both rebalancer paths run the precheck before planning** and, on a hard failure, exit non-zero after the 6.1 backup is already taken. A sliding run that is merely cap-unreachable **proceeds** and reports `over_target_days` (DP-F).

**Acceptance criteria**
- `--range 8-30` parses to offsets `(8, 30)`; a bare `--range 12` parses to `(12, 12)`.
- `--range 0-30`, `--range 30-8`, and `--range abc` each exit non-zero with a message naming the specific problem (`LO >= 1`, `HI >= LO`, malformed).
- `--range 8-30 --start-offset 3` exits non-zero as a mutually-exclusive usage error, and `--help` shows the two as exclusive.
- With `--range 8-30`, cards due outside that window are untouched, absent from the histogram, and reported in the skip summary under `outside --range`; the histogram covers exactly offsets 8..30.
- `anki-due-stats <deck> --range 8-30` reports totals, horizon `D = 23`, and feasible ranges computed on the slice alone — verifiably different from the same command without `--range` on a deck with mass outside the window.
- Omitting `--range` reproduces the pre-range output exactly.
- `--sliding` without both `--min` and `--max` exits non-zero naming both.
- `--sliding --min 8 --max 16 --dry-run` prints a histogram whose per-day targets descend from 16 to 8, and writes nothing.
- A cap-unreachable `--sliding` run completes, reports `over_target_days` and the minimum feasible `--max-shift`, and does **not** raise; the same run with `--strict-sliding` exits non-zero.
- Absent `--sliding`, the flat path is selected and behaves as before (regression check in 6.6).
- `anki-due-stats <deck>` prints all five items, exits 0 on feasible and infeasible decks alike, writes nothing, creates no backup — assert the collection's mtime is unchanged.
- On a block-shaped fixture, `anki-due-stats --sliding` names the worst window and a minimum feasible `--max-shift` in the tens of days, not single digits.
- `due_stats.py` is mode 755, shebang-first, in `package.json` `bin`, with no `except Exception` and no `# noqa`.

**Test approach — oracle: `new contract tests`.**

---

#### 6.6: Verification, including the default-mode regression guarantee

**File scope** — no source edits; this subphase produces evidence.

**The central check.** On a synthetic collection, the **default invocation's scheduling semantics must be identical pre- and post-phase**. Per the scoping at the head of this phase, this asserts on **moves and final card state, not captured stdout**.

**The baseline is captured by 6.1 Work step (a)**, which copies the pre-phase sources to `<parent-worktree>/.artifacts/pre-phase6/` and writes `moves-F1.json`, `moves-F2.json`, `moves-F3.json` for the three pinned fixtures (F1 feasible flat, F2 reverse pass, F3 cap-blocked — all default mode). This subphase only *consumes* those files; if they are absent, 6.1 step (a) was skipped and the regression cannot be verified.

**Acceptance criteria**
- **Default-mode regression:** for each of F1, F2 and F3, the post-phase `{card_id: new_day}` mapping is **byte-identical** to the corresponding `moves-<fixture>.json` captured in step 1. Any difference is a blocking failure, not a discrepancy to explain away.
- The three baseline JSON files exist in `<parent-worktree>/.artifacts/pre-phase6/` and are referenced by path in the exit report.
- **Backup-first, end to end:** a fresh `.colpkg` exists in all three of `--dry-run`, a successful apply, and an `InfeasibleRebalance` exit; the collection is unchanged in the first and third.
- **Precheck ordering:** an infeasible deck exits non-zero having planned no moves, with printed arithmetic matching the core's report.
- **Sparse-deck hard fail (settled DP-B), end to end:** **30 cards spread across 365 days with `--min 8`** exits **non-zero**, writes nothing, creates **no backup**, and the message names the feasible `--min` (here `floor(30/365) == 0`, so the guidance must be to omit `--min` or narrow the window rather than to pass `--min 0`). This is the case that previously succeeded by compacting the queue; asserting the failure is the whole point of the ruling.
- **The three documented escape routes work** on that same fixture: lowering `--min` to a feasible value, **omitting `--min` entirely** (max-only, no lower check), and `--range`-slicing to a window whose density clears the bound — each completes without a precheck failure.
- **Sliding end to end:** every day at or under the **hard** `max`; days above `T(d)` reported in `over_target_days`; `--max-shift` respected; no card on today or earlier.
- **Range containment end to end:** with `--range 8-30` on a fixture holding cards on both sides of the window, every card outside is byte-for-byte unchanged, no move lands outside offsets 8..30 in either direction, and the reported horizon is 23 days.
- **Range + `--set-earlier`:** excess that cannot be absorbed by offset 30 exits non-zero as `InfeasibleRebalance` naming the offending days — the horizon does **not** extend past 30.
- **Range + `--sliding`:** `T(d)` ramps from `max` at offset 8 to `min` at offset 30, and the cap-aware check is computed on the slice.
- **Range + `--max-shift`:** a card due at offset 10 with a 14-day budget lands no earlier than offset 8, never offset 1.
- **Cap-reachability end to end:** a block-shaped fixture reproduces the 6.4 finding — infeasible-to-shape at `--max-shift 14`, reachable at the reported minimum.
- **`anki-due-stats` end to end:** read-only, output matches the core for the same inputs, exit 0 either way.
- **No new lint findings** versus the Phase 1 Step 0 baselines; full pytest suite green with the count reported.
- Manual `anki-due-stats programming::coding` and `--sliding --dry-run` against the **real** collection with Anki closed, both pasted into the exit report. **Dry-run and read-only only — no writes to the user's real collection as part of the build.**

**Test approach — oracle: `equivalence check`** for the default-mode regression; `existing suite` for the lint and pytest gates.

---

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

Every decision point this plan raised has been answered by the user — the original D1-D9 at the first plan gate, and DP-A through DP-F across the Phase 6 gate rounds. **There are no open decisions.** They are recorded here as constraints, and the subphases above already encode them. The identifiers are kept so the review history stays traceable.

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
| **DP-B** | Feasibility precheck severity | **Hard-fail BOTH sides, no escape flag.** `avg > max` and `avg < min` — and their prefix/Hall refinements — each hard-fail **before backup and planning**, printing the arithmetic and a suggested feasible `--min`/`--max`. **There is no `--skip-precheck`.** *User's rationale, recorded:* the strict mental model is preferred — if the numbers do not fit, do not run. Sparse-deck consolidation is reached by lowering `--min`, by **omitting `--min`** (a max-only run has no lower check at all), or by slicing with `--range`. | 6.1, 6.6 |
| **DP-F** | Cap-unreachable sliding shape | **Option 1 — best-effort + report, as the DEFAULT.** Apply the sliding shape as far as `--max-shift` allows, leave the unreachable region above `T(d)`, and report `over_target_days` plus the minimum feasible `--max-shift`. **Never fails on shape alone.** The other two routes stay explicitly reachable and are what the stats command's reporting exists to make *informed choices rather than discoveries*: a larger `--max-shift` (~48+ for the real block, or `none`) achieves the shape at the cost of real interval distortion on mature cards; `--set-earlier` flattens the block by spilling it later, at the cost of moving cards further away. `--strict-sliding` remains the shape-or-fail escape for anyone who wants the opposite default. | 6.3, 6.4, 6.5 |
| **DP-A** | Sliding surface | **Flag (`--sliding`) on the existing command**, not a sibling command — a sibling would duplicate ten flags and need every future safety flag added twice. `anki-due-stats` *is* its own command, being a genuinely different (read-only) operation. `due_plan.py` is not forked either way. | 6.5 |
| **DP-C** | Window (Hall) condition in the precheck | **Included.** On the plan's own flagship infeasible distribution the global average check passes while the window check catches it; omitting it would ship a precheck that clears inputs the planner then refuses. Hard leg uses `max_per_day` capacity; the `T(d)`-fed variant is informational only (B25). | 6.1, 6.4 |
| **DP-D** | Rounding for `T(d)` | **`floor(x + 0.5)`**, explicitly not Python's banker's `round()`, which would make the line depend on parity. | 6.3 |
| **DP-E** | Scope of the "unchanged default behaviour" guarantee | **Scheduling semantics, not stdout** — identical `(card_id → new_day)` move sets and final collection state. Not literal output equality, because this phase's own cosmetic fixes intentionally change printed text. | 6.1 (a), 6.6 |

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
