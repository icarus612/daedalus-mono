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
