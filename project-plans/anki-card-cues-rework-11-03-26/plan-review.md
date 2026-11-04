# anki-card-cues-rework-11-03-26.plan-review

## Round 1 — 11-03-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 5
```

### Findings
- [non-blocking] Hidden dependency under D5 Option B: lane 4 (4.1, mutable templates) would need the `case_tags.py` badge block from 3.2 (lane 3) for Verbs, but 4.1 declares no `after:` edge on 3.2. If D5 = B, add `(after: 3.2)` to 4.1 or split a Verbs-tag subphase.
- [non-blocking] Scope gap: `anki_tools/mutable_words.py:82` concatenates `case_field.CASE_CSS`; 4.5 deletes `CASE_CSS` but its file scope lists only `immutable_words.py` for the CSS concatenation. Add `mutable_words.py` to 4.5 (and its test) or the build breaks.
- [non-blocking] Overlap: 3.3 removes `PROMPT_CASE_ID`, `unless_field` and `add_case_row`, and 4.5 deletes the same symbols. Pick one owner (3.3 is in lane 3 and is the natural one) so 4.5 is only the sweep.
- [non-blocking] 4.1 (lane 4) calls `prompt_hint.add_prompt_hint(..., TRANSLATION_ANCHOR)` while lane 3 edits `prompt_hint.py` (removing `unless_field`). Disjoint files but a shared API; declare that 4.1 uses only the `(html, field, element_id, anchor)` form so lane 3's change cannot break it.
- [non-blocking] UNCERTAIN: the "72 of 369 cues are bare part-of-speech labels" figure. Verified 369 cues and 27 case-naming cues exactly; my crude count of bare POS labels found 65 with a small label set, so 72 depends on the label list used. 2.2 re-proves it, so not blocking.

### Verified
- validate-plan.sh: OK (19 subphases); plan-lifecycle.sh check on the plans dir: OK.
- All 18 cited commits exist. Cited symbols exist: `PROMPT_CASE_ID`, `unless_field`, `add_case_row`, `CASE_CSS`, `GOVERNING_SECTION`, `case_name_for_row`, `residual_info`, `_detail_fields`, `_DETAIL_ID_OVERRIDES`, `ASPECT_COLOURS`, `TRANSLATION_ANCHOR`, the named tests, `review_state`, `pull/rebuild/push`; `main()` is not yet staged. Six TSVs, `immutable_guids.json`, and `source-word-list.md` under `tests/data/` match.
- Ask diff: all five asks covered (duplicates, frozen-meaning report with no revert, case as colour-coded tag, case out of English Distinction, case coverage excluding inflected types). The "case differentiates virtually every word" premise is declined in part under D1 with data and reasoning, which is a recorded departure, not an inversion. D3 Option A (Russian card front without tag) is a recommended option the user decides, against the ask's "maybe both sides".

### Open questions
- None blocking. User decisions D1 to D11 are already enumerated in the plan for the gate.

## Round 2 — 11-03-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 6
```

### Findings
- [non-blocking] 4.8 scope is incomplete against its own acceptance. `git grep -e vocabulary_source -e openpyxl` today also hits `tests/test_entry_point_bins.py:16` (bin map), `tests/test_mutable_words_e2e.py:29,153-157,254-262` (imports `vocabulary_source` and reads the workbook), `tests/test_vocabulary_data.py:190` (asserts the README text contains "vocabulary_source"; 4.8 rewrites that README section), and `tests/test_mutable_words_plan.py:309` (openpyxl purity tuple, harmless). Only `test_vocabulary_source.py` is listed, so "exits 1 over code and tests" cannot pass without out-of-scope edits. Add the first three to 4.8.
- [non-blocking] 4.8 and 4.2 both edit `pyproject.toml` and `uv.lock`, and the Lanes section says 4.8 "runs after 4.2", but the syllabus gives 4.8 only `(after: 4.3)` and 4.2 `(after: 4.1)`. Nothing orders them. Add `4.2` to 4.8's `after:`.
- [non-blocking] 3.3 removes `case_field.add_case_row`, but `tests/test_case_field.py:129-158` tests it and that file is not in 3.3's scope (3.1 owns it in the same lane, so it is a scope omission, not a lane collision). Add it to 3.3.
- [non-blocking] Cell collision between 2.5/4.3 and Phase 6: 2.5 routes forms into Numerals `Gender Forms`/`Genitive` (сорок, девяносто, сто) and Pronouns `Oblique Forms`, but 6.1/6.3 compute `missing` from the pre-4.3 state, where Numerals `Gender Forms` is a dash placeholder in 44 of 55 rows. 6.3 can propose a fill for a cell 4.3 then writes, and 6.4's "no previously non-empty cell changed (vs the 4.3 state)" then fails or the user is asked twice. State that 6.3 excludes cells targeted by 2.5.
- [non-blocking] The census counts "empty" but the TSVs use "—" as the empty marker (nouns Plural 134 are all "—"; adverbs Comparative 23 empty + 37 "—"; adjectives Short Form 151 + 7). The plan's collection counts (Plural 134, Short Form 158, Comparative 165, Verbs Past 177) do match empty-plus-dash, so the importer evidently normalises it, but 6.1 should say so explicitly and assert it, or the TSV census and collection census will disagree in the positive control.
- [non-blocking] Round 1 findings are resolved: 4.1 now has `(after: 1.3, 3.2)`; 4.9 lists `mutable_words.py:82` (verified at line 82); 3.3 is sole owner of `PROMPT_CASE_ID`/`unless_field`/`add_case_row` and 4.9 only sweeps; the `prompt_hint` API is pinned by signature test.

### Verified
- `validate-plan.sh`: OK (30 subphases). `plan-lifecycle.sh check project-plans`: OK (plans dir layout conformant). The script's INFO lines say lane disjointness and ask faithfulness are not machine-checked; both are judged here.
- Lane disjointness (lanes 1 to 5): checked by file. Lane 3 (`case_field`, `case_pill`, `immutable_words*`, `prompt_hint`) and lane 4 (`mutable_words*`, verbs/adverbs TSV headers) are disjoint; lane 4 only calls `prompt_hint` through the pinned four-parameter API; `grep` shows `mutable_words_plan.py` uses neither `PROMPT_CASE_ID` nor `unless_field`. Lane 5 writes only new files. 6.3 reading TSVs while 4.1 changes two TSV headers is a read-only overlap and safe if census keys on header names.
- Code claims: `FIELD_NAMES` has no `Case` on Verbs/Adverbs and Verbs has `Case / Preposition`; `_detail_fields` excludes neither distinction field (so the duplicate-row claim in the card spec holds); `_DETAIL_ID_OVERRIDES`, `_detail_block`, `_ADD_TITLE_FUNCTION`, `_build_extra_css`, `CASE_CSS`/`CASE_ID`/`add_case_row`, `HINT_IDS`, the named tests (`test_the_answer_keeps_a_labelled_russian_distinction_row`, `test_no_duplicate_ids_once_frontside_expands`, `test_empty_cue_renders_nothing_...`) and `card.render_output()` at `test_mutable_words_plan.py:825` all exist. `~/.cache/ms-playwright/webkit-2311` exists; no playwright dependency exists yet, matching "new".
- Data: TSV rows nouns 631, verbs 214, adjectives 172, pronouns 29, numerals 55; Verbs `Case / Preposition` 169 empty so 45 non-empty; Verbs empties 160/160/160/160 and Past 175 + 2 dashes = 177 match the census. Adverbs has 154 TSV rows of which 22 are placeholder rows (headword "—"), consistent with the plan's flagged caveat.
- Ask diff: all later appended entries are covered. Tag as coloured pill is recorded as a gate decision (D7) with the rejected alternatives and reasoning, so it is a recorded departure from the literal word "tag", not an inversion. Pills on both sides for English, back only for Russian (D3) is a recorded option. "No case in English Distinction" is enforced by the 4.6 ban. Coverage with Nouns/Adjectives/Pronouns/Numerals excluded matches the ask. Mutable form fill covers all six mutable types with a missing/not-applicable split. The alignment clarification ("top and bottom centre aligned") is delivered as one centred block sharing the headword's centre line, asserted in 4.7. Meaning freeze with no revert plus a report matches ask item 2.

### Open questions
- None blocking. UNCERTAIN, unchanged from round 1: the "72 cues" figure (2.2 settles it). UNCERTAIN: whether the pill attribute-selector (`[data-case*=... i]`) renders on AnkiMobile; the plan states this itself and checks it at 5.3.
