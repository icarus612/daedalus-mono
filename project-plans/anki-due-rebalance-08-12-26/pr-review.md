# pr-review

## Round 1 — 08-13-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 2
```

### Scope of this review

Full branch diff `main...feature/anki-due-rebalance` (13 files, +4564/-88):
`docs/libs/python/anki-tools/README.md` (new), `libs/python/anki-tools/README.md`
(now a symlink), `anki_tools/__init__.py` (new), `anki_tools/due_plan.py` (new),
`anki_tools/rebalance_due.py` (new), `package.json`, `poetry.lock`, `pyproject.toml`,
`tests/test_due_plan.py` (new), `tests/test_rebalance_due.py` (new), and the three
committed plan records (`plan.md`, `plan-review.md`, `code-review.md`). Spec of record:
`project-plans/anki-due-rebalance-08-12-26/plan.md` (all 11 subphases already ticked
`[x]` in the syllabus).

This is a re-review of work the `code-review` gate already verified independently
across two rounds (round 1: tentative, 5 non-blocking; round 2 post-rework: tentative,
1 non-blocking). Rather than repeat that whole pass, I independently re-ran the
verification commands myself from a clean state and read both new source files end to
end against the plan's pseudocode, rather than trusting the exit report or the code-review
report's prose.

### Independently verified (commands re-run by this gate, not just read from reports)

- `.venv/bin/poetry run pytest -q`: **111 passed** (matches exit report and code-review).
- `ruff check --output-format=concise .` diffed byte-for-byte against
  `.artifacts/baselines/ruff-baseline.txt`: **identical**, zero new findings.
- `python3 -m flake8 --max-line-length=88 .` diffed byte-for-byte against
  `.artifacts/baselines/flake8-baseline.txt`: **identical**, zero new findings.
- `grep -n "except Exception\|# noqa\|TODO"` over `due_plan.py` and `rebalance_due.py`:
  no matches — the conventions section's "no blind except, no noqa, no TODO" holds.
- File modes: `rebalance_due.py` is `755` with `#!/usr/bin/env python3` as its first
  line; `due_plan.py` is a plain (non-executable) module, consistent with only the
  former being a registered `bin` entry.
- `poetry.lock` has `anki` pinned at `24.6.3` (PEP 440 normalization of the declared
  `24.06.3`, exactly as the plan predicted) and `pyproject.toml`/`package.json` diffs
  match the plan's 1.1 Work section line for line (`anki` runtime dep, `pytest` dev
  dep, `[tool.pytest.ini_options]`, `"test": "poetry run pytest"`,
  `"anki-rebalance-due": "anki_tools/rebalance_due.py"`).
- Read `due_plan.py` (345 lines) end to end against the plan's pseudocode for
  `apply_max_pass`, `apply_reverse_max_pass`, `apply_min_pass`, `plan_rebalance`, and
  `_check_post_conditions`: matches line for line, including the subtle bits — one-day
  cascade (never skip-searching for a day with room), untouched-first as the primary
  sort key with the `False < True` trick, the shift cap gated only on the earlier-moving
  passes, the min pass's "keep hunting past a cap-blocked source" behavior (spot-checked
  against `test_apply_min_pass_keeps_hunting_past_a_cap_blocked_source`, the N17 case,
  which matches the plan's acceptance criterion exactly), `sink_overflow` computed
  before the reverse pass but retained after it, and the shared `_reached_exempt_tail`
  helper (code-review round-1 finding 4's fix) used by both `apply_min_pass` and
  `_short_days`.
- Read `rebalance_due.py` (350 lines) end to end: `try/finally` wraps the whole
  collection-open-to-close lifecycle (the plan's deliberate divergence from
  `get_deck_info.py`); `DBError` caught before the broader `AnkiException` (correctly
  ordered per `anki/errors.py`'s inheritance); `InfeasibleRebalance` is caught and
  handled *before* any backup or `set_due_date` call, preserving the D3 "nothing
  written on failure" guarantee; `set_due_date` is called with the non-bang form
  (`str(target_day - today)`, no `!`), grouped one call per target day; backup taken
  via `create_backup(force=True, wait_for_completion=True)` unless `--no-backup`;
  `render_histogram` computes a true `day - today` offset and keys its below-min marker
  off `result.short_days` (both round-1 code-review findings 1 and 2's fixes, confirmed
  present); `collect_cards` has a dedicated `skip_buried` counter (finding 3's fix).
- Read `docs/libs/python/anki-tools/README.md` in full: accurate against the shipped
  code (flag table, invariant description, move mechanics, safety sequencing, test
  count all match what's in `rebalance_due.py`/`due_plan.py`); `libs/python/anki-tools/README.md`
  is now a symlink to it (`../../../docs/libs/python/anki-tools/README.md`), matching
  the `doc-format` mirror/symlink convention. Commit `3fc58ab` touches only these two
  files — no stray edits.
- Commit `65fb4eb` (plan records) touches only the three files under
  `project-plans/anki-due-rebalance-08-12-26/` — no stray edits.
- Working tree is clean (`git status --porcelain` empty) at review time.
- No duplication concern either direction: `due_plan.py`/`rebalance_due.py` implement a
  genuinely new algorithm with no existing equivalent elsewhere in the repo (the plan's
  own Conventions section already establishes there is no cross-`libs/python/*` import
  precedent, and neither file imports from a sibling package); no repeated new logic
  that should have been extracted — the one thing that could have drifted
  (tail-exemption logic) was already factored into `_reached_exempt_tail` during the
  rework round.

### Findings

- [non-blocking] `anki_tools/rebalance_due.py:95` (`render_histogram`) — carried
  forward from code-review round 2's one open finding: the `min_per_day` parameter is
  still present in the signature but no longer referenced in the function body (the
  below-min marker now keys off `short_days_set` instead). Confirmed still true by
  reading the current function. Harmless (neither lint toolchain flags unused
  parameters), but it's dead signature surface across `def render_histogram(...)`, its
  one call site in `main()`, and several test call sites. Worth dropping in a follow-up
  rather than blocking this merge on it.
- [non-blocking] `verify-run-scope.sh <worktree> main .artifacts` reports one
  `UNCLAIMED:` line: `libs/python/anki-tools/README.md`. This is **not** an
  orchestrator-edited-the-product-directly violation — it's the documentation stage's
  own commit (`3fc58ab`, "docs(anki-tools): document the anki-rebalance-due script"),
  explicitly out of lane `l1`'s scope per the plan's own "Out of scope: Documentation"
  section and skill-mapping table (`document-local` owns it, not the build lane). I
  read the full diff (see above): it is exactly the expected symlink + canonical-docs
  pair, content-accurate, nothing else touched. The script only tallies claims from
  lane exit reports (`.artifacts/reports/*.md`), and the documentation stage doesn't
  produce one of those under the `run-artifacts` convention — so this is a tooling gap
  in what the scope-check accounts for, not a scope violation in the diff itself.
  Flagging so it's visible, not blocking the merge on it.

### Open questions

None — both findings above are non-blocking notes with verified explanations, not
decision points that bar a verdict.

## Round 2 — 08-13-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 3
```

### Scope of this review

Fresh full pass over `main...feature/anki-due-rebalance`, re-reading the plan at
`project-plans/anki-due-rebalance-08-12-26/plan.md` at its current state (now 13
subphases, all ticked `[x]`, Phase 5 added by user order after round 1 shipped).
Since round 1: four new commits — `65fb4eb` (plan records: `plan.md`,
`plan-review.md`, `code-review.md`), `26f4eae` (Phase 5 plan amendment),
`66c72e4` (the fix itself), `b2ce132` (syllabus ticks for 5.1/5.2). The Anki
feature files (`due_plan.py`, `rebalance_due.py`, tests, manifests, docs) are
byte-for-byte unchanged since round 1 — this pass re-confirms them are still
intact rather than re-reading them line by line.

`git diff --stat main...feature/anki-due-rebalance` (15 files, +5357/-240) adds
exactly one file to round 1's set: `libs/prompting/claude/hooks/smart-lint.sh`
(+592/-152, matching the exit report's hunk count), plus the three plan-record
files and this report itself growing. No other file changed since round 1.

### Independently verified this round (commands re-run, not read from reports)

- `.venv/bin/poetry run pytest -q` (from `libs/python/anki-tools/`): **111
  passed** — unchanged from round 1, confirming Phase 5's disjoint file scope
  claim.
- `ruff check --output-format=concise .` diffed byte-for-byte against
  `.artifacts/baselines/ruff-baseline.txt`: **identical**, zero new findings.
- `diff libs/prompting/claude/hooks/smart-lint.sh ~/.claude/hooks/smart-lint.sh`:
  **empty output** — the two copies are byte-identical, confirming the
  out-of-repo install landed and matches the reviewed/committed source.
- `bash -n libs/prompting/claude/hooks/smart-lint.sh`: parses clean.
- Read the full hook-mode dispatch path end to end: `TARGET_FILE` resolution
  (CLI bare-path arg or `jq`-parsed stdin JSON) → `should_skip_target` early
  gate (missing file / outside repo / `.claude-hooks-ignore` / non-lintable
  extension → one line + `exit 0`, *before* the header, before `load_config`,
  before any project-type detection) → extension-keyed dispatch in `main()`
  to exactly one of `lint_python_scoped` / `lint_go_scoped` / `lint_javascript`
  (already per-file via its pre-existing `TARGET_FILE` branch) /
  `lint_rust_scoped` / `lint_nix_scoped`. Matches the plan's 5.1 spec exactly,
  including that Go/Rust scope to the nearest enclosing module/crate via the
  new shared `find_nearest_manifest` helper rather than the whole repo.
- Independently reproduced (not just trusted from the exit report): ran
  `bash libs/prompting/claude/hooks/smart-lint.sh README.md` myself → `[INFO]
  Skip (no lintable extension): README.md`, exit 0, and `git status --porcelain`
  empty before and after — the motivating regression is real, live, on this
  branch's committed copy, not only on the installed fork.
- `find_pruned`'s prune-name list contains `.workflows` (confirmed by reading
  the function directly, line 88 in the current file).
- `verify-run-scope.sh <worktree> main .artifacts`: same single `UNCLAIMED:
  libs/python/anki-tools/README.md` as round 1 — no new unclaimed product
  changes from the Phase 5 commit. `smart-lint.sh` itself is correctly
  attributed to lane `l1`'s exit report (Phase 5 section), so it does not
  appear in the unclaimed list.
- `gh pr view 12`: state `OPEN`, `mergeable: MERGEABLE`, not a draft — still
  publishable as-is.
- Working tree clean (`git status --porcelain` empty) at review time.

### Findings

- [non-blocking] Carried forward from round 1, unchanged: `render_histogram`'s
  `min_per_day` parameter (`anki_tools/rebalance_due.py:95`) is still present
  but unreferenced in the body. Re-confirmed present verbatim. Still harmless,
  still worth a follow-up cleanup, still not something this Phase 5 addition
  touched or could have touched (disjoint file scope).
- [non-blocking] Carried forward from round 1, re-verified: `verify-run-scope.sh`
  still reports `libs/python/anki-tools/README.md` as `UNCLAIMED:` — the same
  adjudicated false positive (the `document-local` stage's commit, out of lane
  `l1`'s scope per the plan, and the scope-check script has no report to read
  for the docs stage). No change in status; re-flagging only because a fresh
  scope-audit run was performed this round per the review-pr procedure.
- [non-blocking] `libs/prompting/claude/hooks/smart-lint.sh`'s `lint_python()`
  (CLI-mode, repo-wide path, line 476) gained `.workflows` in its `exclude_dirs`
  string, in addition to `find_pruned`'s prune list gaining the same entry.
  This is disclosed as a "deliberate deviation beyond the plan's literal text"
  in both the contract and the exit report, and the reasoning holds up: `black`
  and `flake8` do their own file discovery via `--exclude`/gitignore rather than
  going through `find_pruned`, and `flake8` in particular has no gitignore
  awareness, so without this addition a CLI-mode run would attempt to sweep the
  ~68,741 `.py` files living under sibling worktrees in `.workflows/` — exactly
  the cost this phase exists to eliminate, and likely enough to fail 5.2(d)'s
  "no sibling worktree descended into" criterion for flake8 specifically. The
  change is narrowly scoped (one CLI-mode exclusion string, Python only, still
  gated by `.workflows` already being gitignored repo-wide) and only *removes*
  scanning of already-ignored code — it does not weaken any check the plan
  cared about. Flagging because it is a real, disclosed expansion past the
  plan's literal instruction, not because it looks wrong on inspection.

### Open questions

None — all three findings above are non-blocking notes with verified
explanations (two unchanged from round 1, one newly surfaced and independently
confirmed reasonable), not decision points that bar a verdict.

## Round 3 — 08-14-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 4
```

### Scope of this review

Fresh full pass over the local `feature/anki-due-rebalance` branch (5 commits
ahead of `origin/feature/anki-due-rebalance` / PR #12 as published — this
review covers what is about to be pushed, per the branch-mode diff
`main...HEAD`) against `project-plans/anki-due-rebalance-08-12-26/plan.md`
re-read at its current state: all 6 phases / 20 subphases ticked `[x]`,
Phase 6's decision table (DP-A through DP-F) all settled, no open decisions.

Since round 2: five new commits landing Phase 6 (user-ordered: early backup,
strict two-sided feasibility precheck, `--range` windowing, `--sliding`
soft-target ramp, cap-aware reachability, `anki-due-stats`) — `e4ff097`
(plan amendment), `98a90ae` (the build: `due_plan.py`/`rebalance_due.py`
+ new `due_stats.py`, 7 files +2900/-102), `faba915` (syllabus ticks),
`223654d` (docs), `5d4d061` (code-review round 3 record, ready/proceed).
`git diff --stat main...HEAD`: 17 files, +9180/-240 — exactly Phases 1-6's
source/tests/manifests, `smart-lint.sh` (Phase 5, disjoint scope), both
README locations, and the four committed plan records. No stray files.

### Independently verified this round (commands re-run, not read from reports)

- `.venv/bin/poetry run pytest -q`: **189 passed** (97 `test_due_plan.py` +
  74 `test_rebalance_due.py` + 18 `test_due_stats.py`).
- `ruff check --output-format=concise .` and `python3 -m flake8
  --max-line-length=88 .`, both diffed byte-for-byte against
  `.artifacts/baselines/{ruff,flake8}-baseline.txt`: **identical to
  baseline** — zero new findings anywhere, including the three Phase 6
  files.
- **Default-mode regression, re-derived independently a second time** (the
  code-review gate already did this once): wrote a standalone script
  reproducing `.artifacts/pre-phase6/gen_pre_phase6_baselines.py`'s exact
  three fixtures (F1 feasible-flat, F2 reverse-pass, F3 cap-blocked) against
  the shipped `anki_tools.due_plan.plan_rebalance`, diffed the resulting
  `{card_id: new_day}` maps against `.artifacts/pre-phase6/moves-{F1,F2,F3}.json`
  by Python dict equality: **F1 (7 moves) / F2 (33 moves) / F3 (24 moves)
  all MATCH.**
- **Safety ordering, read directly in `rebalance_due.py:main()`
  (lines 336-507).** Exact sequence: `resolve_deck_ids` -> `collect_cards`
  (range-aware) -> `check_feasibility` -> (fail: `_print_infeasibility` +
  `SystemExit(1)`, no backup, no `plan_rebalance` call) -> (pass) backup
  block -> `plan_rebalance` -> (`InfeasibleRebalance`: print + exit, still
  no write) -> histogram -> `y/N` confirm (skippable) -> `apply_moves`, all
  inside a `try/finally` that closes the collection. Matches 6.1(b)'s pinned
  order exactly.
- **DP-B/DP-F hard-vs-shape split, read structurally in `due_plan.py`.**
  `check_hard_feasibility` (due_plan.py:599-698) builds its window capacity
  only from `constant_targets(..., max_per_day)` in all three checks (global
  upper, global lower, window/Hall) — never a `DayTargets` line derived from
  `T(d)`. `analyze_shape` (due_plan.py:716-744) is the only caller that
  passes the sliding target line into the shared `window_violations` kernel,
  and its result has no `feasible` field — `check_feasibility` composes
  `feasible=hard.feasible` only. No code path can blend the two.
- **CLI surface read directly against 6.5's spec.** `parse_range` (shared by
  both `rebalance_due.py` and `due_stats.py`) enforces `LO >= 1` and
  `HI >= LO` with per-case messages, accepts a bare `N` as `N-N`; `--range`
  and `--start-offset` sit in an `argparse` mutually-exclusive group on both
  commands; `--sliding` without both `--min`/`--max` hits `parser.error(...)`
  on both commands; `due_stats.py` never imports or calls `create_backup`/
  `set_due_date`/`plan_rebalance`, exits via `SystemExit(0)` on every path
  including "no in-scope cards" and an infeasible pair.
- `due_stats.py`: mode `775`, `#!/usr/bin/env python3` first line,
  registered in `package.json` `"bin"` as `anki-due-stats`; `due_plan.py`
  correctly left non-executable (not a `bin` entry). `grep` for
  `except Exception`, `# noqa`, `TODO`, `skip.precheck` across all three
  Phase 6 source files: no matches — conventions and the settled
  "no `--skip-precheck` escape flag" (DP-B) hold.
- `bash ~/.claude/hooks/verify-run-scope.sh <worktree> main <run-dir>`:
  same single `UNCLAIMED: libs/python/anki-tools/README.md` as rounds 1-2 —
  no new unclaimed product change from Phase 6. Same adjudicated false
  positive: the `document-local` stage's own commit, out of lane `l1`'s
  scope, no exit report exists for the doc stage under the `run-artifacts`
  convention.
- `gh pr view 12`: `OPEN`, `MERGEABLE`, not draft. Note: the local branch is
  5 commits ahead of the pushed PR branch at review time (Phase 6 has not
  been pushed yet) — this review's diff is `main...HEAD` on the local
  branch, i.e. what `push-pr` is about to publish, not the PR as currently
  visible on GitHub.
- Read `docs/libs/python/anki-tools/README.md` (Phase 6 update, commit
  `223654d`) against the actual argparse wiring and flag behavior: the flag
  table, safety-ordering description, sliding/range semantics, and
  `anki-due-stats` output description all match the shipped code. No
  inaccuracies found.
- Working tree clean (`git status --porcelain` empty) before and after this
  review's own verification commands — no collateral drift.
- **Correction to this round's carried-forward-findings expectation:** the
  `render_histogram` dead `min_per_day` parameter, open since code-review
  round 2 and pr-review rounds 1-2, is **no longer present** —
  `def render_histogram(before, after, max_per_day, today, short_days)` is
  now 5-arg, matching 6.1(d)'s explicit "remove it... make the removal
  consistent with [6.3's] direction" instruction. All call sites (1 product,
  9 test) use the new signature; `test_rebalance_due.py:514` pins a
  regression guard asserting the old 6-arg call now fails. This finding is
  resolved, not carried forward.

### Findings

- [non-blocking] Carried forward from round 1/2, re-verified unchanged:
  `verify-run-scope.sh` still reports `libs/python/anki-tools/README.md` as
  `UNCLAIMED:` — the same adjudicated false positive (documentation stage's
  commit, outside lane `l1`'s scope, no exit report exists for the doc
  stage). No action needed; re-flagging per the review-pr procedure's
  fresh-scope-audit requirement.
- [non-blocking] `anki_tools/rebalance_due.py` — `result.short_days` is
  still printed as raw absolute day numbers ("Days still below --min after
  the shift cap: <absolute days>"), unlike `over_target_days` a few lines
  below it, which correctly prints `day - today` offsets. Confirmed
  pre-existing (identical in `.artifacts/pre-phase6/rebalance_due.py`,
  predating Phase 6) and correctly out of 6.1(d)'s scope, which names
  exactly two cosmetic fixes (neither is this one). Not a regression; worth
  a follow-up for consistency with the offset convention Phase 6 established
  elsewhere in the same file.
- [non-blocking] `anki_tools/due_plan.py:285-288` (`_infeasible_reason`) —
  carried forward from code-review round 3: a `--range`-mode reverse-pass
  refusal caused by the containment ceiling (`may_move_later_to`) and a
  genuine `--max-shift` refusal both surface as the same `"shift cap"`
  reason string on `InfeasibleRebalance` (the function only distinguishes
  `start_day` — sink overflow — from everything else). Plan-compliant (6.2's
  acceptance criteria only require the existing exception type and the
  offending days, both satisfied), but a user hitting a `--range`-clamped
  reverse pass sees "shift cap" with no mention of `--range`, which could
  point them at raising `--max-shift` (would not help) instead of widening
  `--range` (would). Worth a third reason value once a call site can
  distinguish the two causes.
- [non-blocking] Test coverage gap, carried forward from code-review round
  3: no test pins `_print_infeasibility`'s `suggested_min == 0` wording
  ("omit --min entirely, or narrow the window with --range") specifically —
  the closest e2e precheck-failure test lands on `suggested_min == 1`. The
  fix itself is correct (independently re-derived by the code-review gate
  against the plan's own worked 30-cards/365-days example), but nothing
  would fail if a future refactor reintroduced the literal
  `Suggested --min: 0` wording the plan forbids.

### Open questions

None — all four findings above are non-blocking notes with verified
explanations, not decision points that bar a verdict.
