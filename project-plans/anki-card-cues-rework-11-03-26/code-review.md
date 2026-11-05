# code-review

## Round 1 — 11-05-26

```
verdict: rejected
next: impl-wrong
blocking: 1
non-blocking: 3
```

### Findings

- [blocking] Lint is not green on files this run authored. `ruff check` reports 13 E501 errors that belong to this run: `libs/python/anki-tools/tests/test_card_dedup.py` lines 55, 63, 69, 116, 125, 198, 368, 459, 467, 471, 480, 485 (12 errors; the file is new in 0e5db4f), and `libs/python/anki-tools/anki_tools/mutable_words_plan.py:991` (docstring line of 101 chars, added by 69bba3d; the 138fd75 version of the file has no line over 88). Plan 4.9 requires ruff green, and the user's CLAUDE.md sets zero tolerance. The l18 exit report listed `mutable_words_plan.py:971` as pre-existing debt; that is wrong, since blame points at this run's commit 69bba3d. Fix: rewrap those lines. Lane: l15 (test_card_dedup.py) and l4 (mutable_words_plan.py). Evidence: `uv run --group dev ruff check . --output-format concise`.
- [non-blocking] Genuinely pre-existing lint debt, untouched by this run's diff: `tests/test_word_audio.py:93` E501, `tests/test_word_qualifier.py:3` F401, and format drift in `anki_tools/elevenlabs_tts.py`, `anki_tools/word_audio.py`, `anki_tools/word_qualifier.py`, `tests/test_word_audio.py`. Confirmed none of these files is in `git diff 138fd75 --name-only`. Out of scope; report only.
- [non-blocking] `anki_tools/data/russian-vocabulary/form-fill.tsv` header comment says "Excluded cells (plan list (case-text-routing.tsv not yet committed))". The file is committed now and the l13 exit report says the exclusions were re-run at 6.4. The header is stale text in a committed record.
- [non-blocking] Plan deviations, all user-decided and recorded in the progress log, none of them defects: 4.4 (пожаловать audio) deferred to the user because ELEVENLABS_API_KEY was unavailable; 88 form-fill cells left `unresolved` and blank (plan 6.3 allows this); the 4.5 exemptions (Category=gloss, short-label cues) approved at the gate. Docs still reference `vocabulary_source` and `openpyxl` (`docs/libs/python/anki-tools/README.md`, `docs/libs/python/anki-tools/mutable-words.md`), which is the Record stage's job per plan 4.9. Phase 5 (5.1 to 5.4) has not run and is outside this gate.

### Verified

- Full suite in the lane-merged worktree at c40cf06: 2779 passed, 17 skipped, 0 failed (run by me).
- Dangling-reference sweep `git grep -e vocabulary_source -e openpyxl -e prompt-case -e PROMPT_CASE_ID -e unless_field -e add_case_row -e CASE_CSS` exits 0 with hits (positive control: the pattern works). Every hit in code and tests is a negative assertion (test_prompt_hint, test_case_field, a purity test) or the docs, none a live reference. Production code has no hits.
- Tree is clean, no uncommitted changes. Sync script diff read in full: staged pull/rebuild/push, snapshot guard, and Anki-running and credential handling behave as plan 1.1 specifies; credentials remain in memory.
- Meaning-freeze test and its seeded-edit positive control exist (`test_qualifier_classification.py:265,276`); GUID pin tests exist and pass, including the так re-key.
- `form-fill.tsv`: 2267 missing-filled and 88 unresolved, matching the exit report and the 6.4 count; every row has a source and licence recorded in the header.
- Comment hygiene: 5 added comment lines in source and 12 in tests, not a banner-comment violation.

### Open questions

- None blocking. For the user: the pre-existing lint debt (non-blocking finding 1) can be fixed in a separate change if wanted.

## Round 2 — 11-05-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 1
```

### Findings

- [non-blocking] Pre-existing lint debt remains, outside this run's diff (confirmed absent from `git diff 138fd75 --name-only`; positive control on the same command finds test_card_dedup.py): `tests/test_word_audio.py:93` E501 and `tests/test_word_qualifier.py:3` F401. Separate change if wanted.

### Verified

- Round 1 blocking finding resolved: `ruff check .` at 8cbe342 reports only the two pre-existing hits above; the 13 E501 errors in test_card_dedup.py and mutable_words_plan.py are gone. test_card_dedup.py: 25 passed.
- Stale form-fill.tsv header fixed (now names the exclusion cells directly).
- Worktree clean apart from this report.

### Open questions

- None.
