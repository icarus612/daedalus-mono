# pronoun-two-sided-form-cards-11-22-26.plan-review

## Round 1 — 11-22-26

```
verdict: rejected
next: plan-wrong
blocking: 1
non-blocking: 5
```

### Findings

- [blocking] The plan still treats D10 as undecided and builds its headline numbers on option A, although the last Ask of record entry records the user's decision "replace them and just keep the 60" (D10 = B). Evidence:
  - Goal & scope "In scope" says "214 existing form cards kept and 29 removed (D10-A; or all 243 replaced under D10-B)" and "196 new cards dated one per day from due 2153".
  - "Decided by the user (11-22-26)" omits D10, and the Decision points section still lists D10 as open, with A as "the user's stated default".
  - Conventions "Existing cards" and the 5.1 acceptance lead with A: 214 kept, 29 removed.
  - Under the decided B the correct figures are all 243 removed, 410 new cards dated 1937 to 2346, and a 437-day horizon. Those figures exist in the plan but only as the alternative.
  - The Ask of record says the other decisions proceed at the recommended options, so those should move to "Decided" as well.
  - Fix: make B the plan's one path (scope, conventions, 5.1 and 5.3 acceptance, risks), move D10 to "Decided", and drop `--mode keep` or leave it clearly out of scope. Route: `plan-wrong`.
- [non-blocking] 3.1 says `phrase_words` resolves pronoun forms "from the TSV columns, not the derived `Form k` note fields". `phrase_words.taught_word(note_id, field_names, fields)` (`phrase_words.py:232-260`) is a pure function over one collection note's fields. It reads `INFLECTION_FIELDS`, which today includes `*PRONOUN_FORM_FIELDS` (`:72`). Those 44 note fields are deleted, so pronoun forms would silently stop resolving. Reading the TSV inside this pure module is a new data path the plan never describes. The simpler route is to put `Form 1..11` in `INFLECTION_FIELDS`, with the headword still coming from `HEADWORD_FIELDS`. The plan should name the mechanism, because the acceptance test ("a phrase containing кото́рой resolves") is the only guard.
- [non-blocking] `Form k Cases` is specified as `div.case-row[data-cases][data-qual]` containing "tag span + pill spans", while the single-row shape puts the tag after the gloss via `Form k Tag`. For a single-qualifier word, the tag span must be absent from `Form k Cases`, or the tag renders twice. 2.1 and 2.2 do not state this, and the acceptance line "rows equal the Case rows table" does not catch it. Add an explicit assertion for тем (two rows, bare gloss) and той (one row, tag after the gloss, no tag span in the pill line).
- [non-blocking] The 4.2 preview list has "он его́" but the Ask of record asked for "он Genitive after a preposition". Under the per-distinct-word unit that is the separate него́ card, and it carries the `(after a preposition)` purple tag. Add него́ (both sides) to the 4.2 set.
- [non-blocking] Appendix and Live state cite "192 distinct words across the deck". I recomputed the distinct stress-stripped pronoun audio words (30 headwords plus 205 forms, deduplicated) as 219. The 57 words with no `_f1.mp3` in the live media dir, the +61 list delta (1603 to 1664) and the 4 homograph pairs all reproduce exactly, so the 61 words / 122 requests are sound. Only the "192" label is unexplained. Separately, words such as то, те, все, всё, том, тем, чем and сами already have clips from other notes and will be reused by bare slug. Their stress is unchecked, as with сам, so 5.2 should extend the listening check to any pronoun clip that predates this run and is shared with a non-pronoun note.
- [non-blocking] The Risks section calls `col.get_empty_cards()` and `col.remove_cards_and_orphaned_notes` "unverified for 26.8.1". Both exist in the installed `anki` 26.8.1 (`.venv/.../anki/collection.py:618, 627`), along with `add_field`, `remove_field`, `reposition_field`, `close_for_full_sync`, `reopen`, `full_upload_or_download` and `sync_collection`. The unverified marker can go, and under B only the by-id removal is needed. Not re-verified by me: the live-vs-repo template identity (ords 0-3 byte-identical to `83b8aef`), the verb 294-character duplication, and the 20 overflow pixel widths. They come from the planner's scratch probes. They are UNCERTAIN to me, but nothing load-bearing rests on them, because the grid defect is confirmed in code (`mutable_words_plan.py:1147`, `width: max-content` at `:1150`).

### Open questions

- None blocking a verdict. Please confirm the intended start of the dating under B: the plan uses 1937 (the day after the word cards' max due 1936). The first brief said "after the last existing pronoun date (2152)", but those 243 cards are being removed.

### Structural and verification digest

- `validate-plan.sh`: OK, 16 subphases. `plan-lifecycle.sh check project-plans`: OK, plans dir layout conformant.
- Parallelizability: the lane scopes are disjoint. Lane 1 holds `mutable_words_plan.py`, `case_pill.py`, `mutable_words.py`, the TSV and their tests. Lane 2 holds `form_census`, `form_fill`, `phrase_words`, `source_drift` and their tests. Lane 3 holds `mutable_words_audio`, `flagged_audio_cli`, `audio_naming` and their tests. The hidden-dependency check turned up nothing missed. `variant_pairs`, `immutable_words` and `test_case_coverage` only call `add_pill_block`/`pill_block()` without `trailing`. `trailing` is used only in `case_pill.py`.
- Verified against code or data:
  - All cited line numbers in `mutable_words_plan.py`, `mutable_words.py` and the 18 test assertions I sampled.
  - The TSV: 31 columns, 22 slot columns, 243 filled cells.
  - Appendix A: I re-derived 205 distinct non-base words and every per-pronoun count. There are no same-letters/different-stress conflicts within a pronoun. The only cross-pronoun conflicts are the four сам/самый pairs.
  - Per-ord card counts (27, 27, 26, 22, 17, 17, 16, 14, 14, 14, 11, summing to 205) and the horizon arithmetic (437 and 439 days).
  - Live copy: 55 fields, 24 templates, 303 cards with the stated per-ord counts, max due 2152, word-card max 1936, 243 type-4-only revlog rows on form cards, 0 flagged, 0 `usn=-1`.
- Ask diff: the unit, the pill/tag rule, base-word handling, "(never changes)", the word-card rebuild, five full declensions, N=11 / 24 templates and the migration are all delivered. The requested mockups are present. No inversions found. Recorded, reasoned choices (D9, D9b) are not blocking. The one divergence is the stale D10 above.

## Round 2 — 11-22-26

```
verdict: tentative
next: proceed
blocking: 0
non-blocking: 5
```

### Findings

- [non-blocking] Dating start diverges from the ask's wording and rests on a quote I could not find. The final Ask of record directive says to date every card "one per day after the last existing date". With the 243 cards removed (D10 = B), the last existing pronoun date is the word cards' 1936, but the plan starts at today+1 (1910), overlapping 1910-1936. The plan records this in "Dating order (D3)" and justifies it with a user quote ("one of the new cards due a day ... so none are in new"). That quote is not in the archived plan `completed/pronoun-case-cards-rework-11-21-26.md` or in the memory dir. A positive control on "none left new" does hit in the archive (lines 30, 101, 265), so the zero for the quote is real. The archive's own rule (line 265) is "continuing after the last existing case-card date". The plan treats D3 as decided, but the start date was never shown to the user as a choice. The divergence is recorded with reasoning, so it is not blocking. It does need the user's explicit yes at the gate. Alternative: 1937-2346, a 410-day horizon either way.
- [non-blocking] A 2.1 acceptance property contradicts the plan's own mockups. The property reads: "`Form k Tag` is non-empty if and only if `Form k Cases` has exactly one row and that row has no tag span". For меня́, ты's тебя́ and the other unqualified single-row words, the row has no tag span because the word has no qualifier, and `Form k Tag` is empty. The right-hand side is true and the left is false, so the property test fails on real data. It should read: Tag is non-empty iff the word has exactly one row AND that row has a qualifier (the tag having moved out of the pill line).
- [non-blocking] The `after:` edges from lanes 2 and 3 to 2.1 sit inside lane 1's serial chain (1.1, 2.1, 2.2 to 2.5). A lane merges back whole, so lanes 2 and 3 cannot start until lane 1 finishes unless the dispatcher splits lane 1 at 2.1. The plan should say which. Scopes are disjoint and no missed dependency edge turned up (`PRONOUN_FORM_AUDIO_FIELDS` and `PRONOUN_CARD_SLOTS` consumers are `mutable_words.py` for 2.5, `flagged_audio_cli.py` for 3.2 and `phrase_words.py` for 3.1, all covered).
- [non-blocking] The test fixtures that write a pronouns TSV or pronoun note (`test_source_drift.py` `write_source`, `test_phrase_words.py`, `test_form_census.py`, `test_flagged_audio_cli.py`) carry the old `Gender Forms` / 22-slot header. `parse_pronouns` reads `row["Gender Forms"]` (`mutable_words_plan.py:790`) and breaks once 1.1 drops the column. 3.1 and 3.2 only name count edits, not the fixture header change. The builders will find it, but the contract should say so.
- [non-blocking] The ask says to use the same ids as the verb templates. Verb cards have one `#perfective` line, while the pronoun lines use `form-<j>` ids, which the plan justifies (a card has several lines) and copies the CSS for. That is a recorded, reasoned departure and fine. It should be named at the 4.2 sign-off so the user sees it was deliberate.

### Open questions

- Does the user want form-card dating to start at today+1 (1910, the plan's choice) or after the word cards' last due date (1937), as the final ask wording reads? The plan's quoted justification for today+1 could not be located in the archived plan or memory.
- The shared-clip listening list (всего, всё, ничего, то, чем, это) comes from the planner's probe. I did not re-run it, so it is UNCERTAIN to me. 5.1 re-runs it against the snapshot, which is the right gate.

### Structural and verification digest

- `validate-plan.sh`: OK, 16 subphases. `plan-lifecycle.sh check project-plans`: OK, plans dir layout conformant.
- Round-1 findings: all six are folded in. D10 = B is the single path, with "Decided" updated. The `phrase_words` mechanism is named (`INFLECTION_FIELDS` with `Form 1..11`). The duplicate-tag rule is stated, with the тем and той assertions. него́ is in the 4.2 set. The 192/219 label is explained. The listening check is extended. The "unverified" marker for `remove_cards_and_orphaned_notes` is gone.
- Re-derived from `pronouns.tsv` plus the Appendix B cells parsed from the plan:
  - 30 rows, 22 slot columns, 243 filled cells now. The 14 nominative rows and 5 oblique rows give 42 + 90 = 132 new cells, so 375.
  - 205 distinct non-base words, with the per-pronoun counts matching Appendix A.
  - No same-letters/different-stress conflict inside any pronoun.
  - Per-ord counts 27, 27, 26, 22, 17, 17, 16, 14, 14, 14, 11 sum to 205, so 410 form cards plus 60 word cards is 470 and the mutable total is 3161 - 303 + 470 = 3328.
  - Field arithmetic: 11 - 1 + 2 + 44 = 56. Migration adds 46 and removes 45, so 55 + 46 - 45 = 56.
  - Canonical order puts тем at тот's Form 8, so ord 20 resolves to тем.
  - The тем, того́, тех and той line sets in the mockups match the D11 shared-case rule.
- Line cites sampled and matching: `test_mutable_words_plan.py:174/183/231`, `test_vocabulary_data.py:151/368`, `test_source_drift.py:277`, `test_card_dedup.py:515`, e2e `:61/114/286/326`, `mutable_words.py:47/57`, `phrase_words.py:58-72/232-260`, `flagged_audio_cli.py:84-86`. Stack: `anki` 26.8.1 at `uv.lock:239-240`, `playwright==1.61.0`, and `Collection.remove_cards_and_orphaned_notes` present.
- Parallelizability: the lane scopes are disjoint (lane 1 plan/case_pill/mutable_words/TSV and tests; lane 2 census/fill/phrase/drift; lane 3 audio, flagged, naming).
- Ask diff: nothing is missing, nothing is inverted, and nothing is delivered that was not asked. The Appendix B stress and morphology looked correct on a read.
- Not re-verified by me, taken from the planner's scratch probes: live-vs-repo template identity, the 20 overflow pixel widths, the shared-clip list, and the 57 clip-less words (round 1 reproduced the 57 and +61).
