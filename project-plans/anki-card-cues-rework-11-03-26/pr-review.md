# pr-review

## Round 1 — 11-05-26

```
verdict: rejected
next: impl-wrong
blocking: 1
non-blocking: 2
```

Severity profile: none supplied (default policy). Mode: branch diff `main...feature/anki-card-cues-rework`, no PR (local-only run).

### Findings

- [blocking] `libs/python/anki-tools/tests/test_form_census.py:913-916` (`TestRealData::test_live_collection_reconciles_with_tsv`) fails on the shipping machine. Evidence: `uv run --group dev pytest -q` gives `1 failed, 2778 passed, 17 skipped`; the assertion diff is `{'Verbs': ()} != {'Verbs': ('t1#RNs`=(A',)}`. The test reads the user's live Anki collection and hard-codes its pre-import state: `PENDING_IMPORT_VERB_GUID` still unbuilt, and the 5 orphaned Nouns (`ORPHANED_NOUNS`, line 921-925) still present. Step 5.1 then imported пожаловать and deleted the 5 orphans (progress-log 5.1 line), so the live collection no longer matches. The test is environment-coupled and red at merge time. Fix: assert against the post-5.1 state (no unbuilt, no orphans) or build a scratch collection instead of reading the live one. Reality-checkpoint rule: zero red.
- [non-blocking] Pre-existing lint/format debt, outside this diff (`git diff main...HEAD --name-only` does not list these files): `tests/test_word_audio.py:93` E501, `tests/test_word_qualifier.py:3` F401, `anki_tools/elevenlabs_tts.py:113` would be reformatted. Every file in the diff passes `ruff format --check` (41 files) other than the two deleted ones, which no longer exist.
- [non-blocking] Plan state: 4.4 and 5.2 are `[done]` but the audio was not generated (deferred to the user, recorded in the plan as "done differently"). Accepted as a user decision; the 4 пожаловать audio refs in the mutable package stay unattached until the user runs `word_audio пожаловать --mode single`.

### Verified

- Scope ledger: `verify-run-scope.sh` prints `OK: all 68 changed files claimed by 20 exit report(s) or harness-owned`; no UNCLAIMED lines.
- Completeness against the syllabus: every subphase is evidenced in the diff (case pills `case_pill.py`, `case-government.tsv`, `case-text-routing.tsv`, `qualifier-classification.tsv`, `form_census.py`, `form_fill.py`, `form-fill.tsv`, `source_drift*.py`, staged sync, workbook importer and `vocabulary_source.py` deleted, tests for dedup/ban/coverage/layout). Docs updated under `docs/libs/python/anki-tools/`.
- Workbook retirement: `vocabulary_source.py` and its test are deleted in the diff; no regression seen in the rest of the suite (2778 pass).
- The superseded plan `proposals/anki-outstanding-fixes-10-29-26.md` is deleted and the plan's Goal section names it.
- Plan checkboxes 5.1, 5.3, 5.4 match the progress log (rebuild, drift 0, full upload at 08:32:47).
- No attribution trailers or secrets seen in the branch commit subjects.

### Open questions

- None.

## Round 2 — 11-05-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 2
```

Severity profile: none supplied (default policy). Mode: branch diff `main...feature/anki-card-cues-rework`, no PR (local-only run).

### Findings

- [non-blocking] Carried from round 1, unchanged: pre-existing lint/format debt outside this diff (`tests/test_word_audio.py:93` E501, `tests/test_word_qualifier.py:3` F401, `anki_tools/elevenlabs_tts.py:113` format).
- [non-blocking] Carried from round 1: 4.4 and 5.2 are `[done]` with audio deferred to the user (`word_audio пожаловать --mode single`); accepted as a user decision.

### Verified

- Round-1 blocking finding resolved: commit b295d00 rewrites `test_form_census.py::TestRealData::test_live_collection_reconciles_with_tsv` to assert `unbuilt == {s: () ...}` and `orphans == {s: () ...}` (post-5.1 state). It adds a positive control: dropping one Verbs guid from the collection must yield that guid in `unbuilt["Verbs"]`, so the empty assertions can fail. It also checks the collection file is not mutated.
- Re-ran `uv run --group dev pytest -q` in `libs/python/anki-tools`: `2779 passed, 17 skipped, 0 failed`.
- `verify-run-scope.sh`: `OK: all 69 changed files claimed by 21 exit report(s) or harness-owned`; no UNCLAIMED lines.

### Open questions

- None.
