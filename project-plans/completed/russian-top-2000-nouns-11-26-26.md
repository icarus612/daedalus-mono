# Russian top-2000 nouns, plus a Degrees column

### Ask of record

**11-26-26** — i want you to actually fine the 2000 most common nouns in russian and create cards for them i also want a degrees of seperation column in our local/personal table that says how close the word is to english (between 0-3) 0 being vertually identical 3 being no similarities.

**11-26-26 — appended, follow-up on row style (verbatim fragment, as relayed by the coordinator)** — the style is the one we have for the ~500... right?

**11-26-26 — appended, at planning, scheduling of the closest nouns** — add any with a 0 or 1 value to be due at a rate of 10 new cards a day (after the current ~10 days i have left)

**11-26-26 — appended, at the plan gate, decisions on homonyms and cues** — yes skip indiclinable nouns we already have... and add cues for russian sides and english sides for collisions, if i can be a noun or adj add it to both, and put (noun/adjective) by it on the russian side (or english side if needed)  same with words that have the same spelling as other words...

**11-27-26 — appended, category nouns first** — Make a list of nouns for days of the week months of the year colors foods and household items. ... those items should be the ones that are due next in nouns when I start adding nouns to be done next, they should be top of the list in new

**11-27-26 — appended, order** — The order for new should be days of the week, months ofthe year, colors (maybe thats adjectives too for those?)  then all the household items and food.

## Phase syllabus
- [x] Phase 1: Intake tooling and the skeleton
  - [x] 1.1: `noun_intake` module: candidates, forms, fragment validator, merge            (lane 1)
  - [x] 1.2: Fetch the sources, generate the skeleton and the candidate report               (lane 1, after: 1.1)
- [x] Phase 2: Row drafting
  - [x] 2.1: Batch A: new rows, quarter 1, and Degrees for existing rows 1–158               (lane 2, after: 1.2)
  - [x] 2.2: Batch B: new rows, quarter 2, and Degrees for existing rows 159–316             (lane 3, after: 1.2)
  - [x] 2.3: Batch C: new rows, quarter 3, and Degrees for existing rows 317–474             (lane 4, after: 1.2)
  - [x] 2.4: Batch D: new rows, quarter 4, and Degrees for existing rows 475–631             (lane 5, after: 1.2)
  - [x] 2.5: Adjective and adverb rows for the nouns that are also adjectives                (lane 6, after: 1.2)
- [x] Phase 3: New-card scheduling tool
  - [x] 3.1: `anki-new-due`: dates new cards at a per-day rate                                (lane 1, after: 1.2)
  - [x] 3.2: GUID pins for Mutable rows whose headword gains a qualifier                     (lane 1, after: 3.1)
- [x] Phase 4: Integration
  - [x] 4.1: Add the Degrees column; merge the noun, adjective and adverb fragments          (after: 2.1, 2.2, 2.3, 2.4, 2.5)
  - [x] 4.2: Qualify existing same-spelling rows, pin their GUIDs, rekey their cue rows      (after: 4.1, 3.2)
  - [x] 4.3: Pinned counts, freeze baseline, GUID uniqueness, full suite                     (after: 4.2)
  - [x] 4.4: Regenerate the similarity table and list the new collisions, both sides         (after: 4.3)
- [x] Phase 5: Cues for new collisions, both sides
  - [x] 5.1: Draft English and Russian cues, show one approval table                         (after: 4.4)
  - [x] 5.2: Write the approved cues, regenerate, byte-diff the rest                         (after: 5.1)
  - [x] 5.3: README cue rules: part-of-speech labels allowed for same-spelling words         (after: 5.2)
- [x] Phase 6: Offline build check
  - [x] 6.1: Dry-run counts, build against a collection copy, scratch import                 (after: 5.3)
- [x] Phase 7: Audio
  - [x] 7.1: Dry-run the request count, confirm, generate                                    (after: 6.1)
  - [x] 7.2: Gap-check every new clip with a validated checker, re-roll the broken ones      (after: 7.1)
- [x] Phase 8: Live apply
  - [x] 8.1: Pull, close Anki, back up, source-drift check                                   (after: 7.2)
  - [x] 8.2: Build both packages and run `--stage rebuild`                                   (after: 8.1)
  - [x] 8.3: Sync up and verify                                                              (after: 8.2)
- [x] Phase 9: Schedule the Degrees 0–1 nouns
  - [x] 9.1: Build the ordered list, dry-run, show the histogram                             (after: 8.3, 3.1)
  - [x] 9.2: Apply, counterpart check, sync                                                  (after: 9.1)
- [x] Phase 10: Record
  - [x] 10.1: README, docs page and changelog                                                (after: 9.2)

## Goal & scope

**Goal.** Every noun among the 2,000 most frequent Russian nouns becomes a Mutable Nouns card that follows the existing `nouns.tsv` row style. A noun that is also an adjective gets an adjective card as well, and that adjective gets its adverb when one exists. Every word that shares a spelling with another card carries a part-of-speech label on its Russian side. `nouns.tsv` gains a `Degrees` column (0–3, closeness to English) for every row, both existing and new. The Degrees column is not shown on cards. New nouns with Degrees 0 or 1 are made due at 10 cards a day, starting after the current queue (D5, D6).

**In scope.**
- Frequency source: Lyashevskaya & Sharoff 2009, the RNC frequency dictionary (`http://dict.ruslang.ru/Freq2011.zip`, `freqrnc2011.csv`). It is a TSV: `Lemma`, `PoS`, `Freq(ipm)`, … Nouns are `PoS == "s"`; `s.PROP` (proper names) is excluded. Take the top 2,000 by ipm. The cutoff is нежность at 23.3 ipm.
- **Re-verified while planning** (planner probe, scratch copy of the csv). A lemma matches when stress is stripped, ё is folded to е, and any editorial qualifier `(…)` is stripped. On that rule, **535** of the 2,000 are already in `nouns.tsv` and **1,465** are missing. The coordinator's figure was 534/1,466. The difference is `правда (noun)`: it only matches once the qualifier is stripped, and 1.1 must strip it.
- Of the 1,465 missing:
  - 12 already exist as Immutable rows in `tests/data/source-word-list.md`. Ten are indeclinables already in the `Indeclinable Nouns` deck: кино, кофе, радио, метро, пальто, интервью, кафе, шоссе, такси, бюро. The other two are пора and привет.
  - 8 share a spelling with a row in another Mutable sheet: тысяча, больной, русский, знакомый, зло, тепло, печь, стать.
  - About 36 of the top 2,000 have adjective endings (будущее, учёный, животное, рабочий, столовая, святой …). Plural-only examples are данные and близкие.
  - These classes were decided at the plan gate (D1–D3, now resolved below).
- New rows take the **exact style of the existing 631 rows**. The user said: "the style is the one we have for the ~500... right?" So there is no per-batch style review. Cues are separate; see Phase 5.
- `Degrees` lives in `nouns.tsv` only, for all nouns. It is **not** a note field, and it is not on cards. Scale and the user's anchors:
  - 0 = virtually identical (телефон, автор)
  - 1 = clear cognate (федерация, министр, церковь)
  - 2 = distant / a hint (брат, нос, вода)
  - 3 = no similarity (стол, город, дом)
  - Only what a learner would notice counts.
- **Same-spelling words** (D1 as decided). Each new noun that shares a spelling with another card gets a ` (noun)` qualifier in `Russian`. The existing card on the other side gets its own qualifier where it lacks one. The qualifier is the Russian-side label, because every note type's `Russian Distinction` field is `distinction.qualifier_of(headword)`. The planner verified this in `mutable_words_plan.py` (`NounRow`/`AdjectiveRow`/`AdverbRow`/`NumeralRow.fields`) and `immutable_words_plan.py` (`FIELD_NAMES` includes `Russian Distinction`, filled by `qualifier_of`). So every note type involved already has the field, and no schema change is needed.
  - New noun rows: пора, тысяча, больной, русский, знакомый, зло, тепло, печь, стать, each as `<word> (noun)`. This user request reverses the earlier proposal to drop стать.
  - Existing rows that gain a qualifier, as an explicit user request, with glosses still frozen:
    - adjectives больной, русский, знакомый → `(adjective)`;
    - adverbs зло, тепло → `(adverb)`;
    - verb печь (Imperfective cell) → `(verb)`;
    - numeral тысяча → `(numeral)`;
    - Immutable Base Adverb пора → `(adverb)`;
    - verb стать is a Perfective cell, see D10;
    - plus any further same-spelling pairs that 1.2 or 2.5 surfaces.
  - Skipped: the 10 indeclinables already in the Immutable deck, and привет (the interjection is already a card).
- **Nouns that are also adjectives go in both decks** (D2 as decided). These are будущее, учёный, животное, больной, русский, знакомый, святой, близкие, and the rest of 1.2's `adjectival` class.
  - The noun row goes in `nouns.tsv`.
  - The adjective (its masculine lemma, e.g. будущий for будущее) goes in `adjectives.tsv` if it is missing.
  - When the two spellings coincide, both rows are qualified, `(noun)` / `(adjective)`.
  - Per memory `adjective-adverb-pairs`, each **new** adjective also gets its derived adverb in `adverbs.tsv`. The exceptions are adjectives with no real adverb, which are listed. Adjective/adverb pairs themselves need no cue (README).
- Similarity-table regeneration. Cues are written for genuine new collisions on **both sides**:
  - the English side: the `English Distinction` cue, for English-gloss collisions;
  - the Russian side: the qualifier → `Russian Distinction`, for same-spelling collisions.
  - The user allows a part-of-speech label as the cue where that is what separates the words (`(noun)` / `(adjective)`). This is an override of the README rule "never names a part of speech", and 5.3 updates the rule text.
- Audio for every new headword. Live apply with backup and sync. Placement in the existing Nouns deck. Tests.
- The Degrees 0–1 scheduling the user added. Interpretation (stated per the coordinator, open in D5):
  - "10 new cards a day" means both cards of a note on the same day, so **5 nouns/day**.
  - Order is corpus frequency, most common first.
  - The first due date is **2026-12-07**: day 11 counted from 2026-11-26, after the current force-due queue.
  - Only nouns added by this run qualify. The 535 existing nouns are not rescheduled. Degrees 2–3 new nouns stay new.

**Out of scope.**
- Rewording any existing gloss, cue or Additional Info (memory `never-change-english-glosses-unasked`, `similarity-updates-touch-only-changed-rows`). Existing rows gain only two things: their `Degrees` cell, and, for the named same-spelling rows only, a qualifier in the Russian headword.
- Degrees for the new adjective and adverb rows. Degrees lives in `nouns.tsv` only.
- Showing Degrees on cards. No note-type or template change.
- Examples for new rows. All 631 existing rows have an empty `Examples` cell; the planner checked with `awk` (0 non-empty), so "exact style" means empty.
- Proper names (`s.PROP`). Any rescheduling of existing cards.
- Opening a PR. Per the repo `CLAUDE.md`, this repo lands by local squash-merge into `main`.

## Stack & MAJOR versions
- Python `>=3.11`, package `anki-tools` built with hatchling and run with `uv`. Source: `libs/python/anki-tools/pyproject.toml`.
- `anki` (unpinned; installed in the uv env), `requests>=2.28.0`, dev `pytest` and `playwright==1.61.0`. Source: `pyproject.toml`.
- Test runner: pytest, `testpaths = ["tests"]`. Lint: `py-lint` (ruff) plus the smart-lint hook (black + flake8, max line 88). Source: `package.json` scripts; memory `smart-lint-hook-fires-repo-wide`.
- The JS wrapper is pnpm workspace (`package.json` `devDependencies: lib.bash.build-tools: workspace:*`). The `bin` map there is a shared touchpoint, and only lane 1 edits it.
- TTS: ElevenLabs through `anki_tools/elevenlabs_tts.py`. Voice slots `f1` and `m2` (`mutable_words_plan.VOICE_SLOTS`).

## Conventions to enforce
1. **The TSVs are the only source** (`anki_tools/data/russian-vocabulary/README.md`). Rows are edited in place. New rows get `Status` = `New`.
2. **House stress format** (`form_fill.house_stress`): an acute on the stressed vowel, no mark on ё, no mark on single-vowel words. `—` means no plural (134 existing rows use it).
3. **Existing values are frozen**: every non-Degrees cell of the 631 existing rows stays byte-identical. Existing cues and translations are never rewritten. The single exception is a qualifier appended to the Russian headword of the named same-spelling rows (4.2), which the user requested explicitly. Those rows keep their GUID through a pin (convention 7).
4. **English is English only**: no Cyrillic in `English` (memory `no-russian-in-english-fields`). Use no top-level separators other than ` / ` (`tests/test_gloss_separators.py::test_tsv_english_columns_carry_no_top_level_separator`). Parentheticals do not stay in the English; they move to the cue or to Additional Info (README cue rules).
5. **Homonyms are wanted** (memory `russian-homonyms-are-wanted`). A noun whose spelling exists in another sheet or deck gets a ` (noun)` qualifier in `Russian`, following the existing `правда (noun)` row. It is never skipped or merged. Audio is shared through `audio_naming.strip_qualifier`.
6. **Cue rules**, from the README, `similarity-groups.tsv` as the authority, and memories `disambiguators-minimal-not-sprayed`, `cues-uniform-register-frame`, `cues-no-examples-no-jargon`, `show-card-text-before-writing`:
   - cue only words whose `told apart by` is `cue`;
   - no examples, no nested brackets, no grammar shorthand;
   - partner cues must sound different;
   - show the before → after table before any write.
   - Part-of-speech labels ((noun), (adjective), …) are allowed, by user override, where they are what separates same-spelling words. On the Russian side they are the qualifier; on the English side they are used only where needed.
7. **GUIDs are deterministic** (`anki_identity.guid_for_row(russian, sheet)`, hashing the **qualified** headword; see the `headword_text` docstring in `mutable_words_plan.py`). A headword that collides inside a sheet would silently merge notes on import. Adding a qualifier to an existing headword **changes its GUID**. Without a pin, the import would add a duplicate note, and the studied note would keep its history under a stale headword. The Immutable side already solves this with `immutable_words_plan.GUID_PINS` (`("Base Adverbs", "так (adverb)"): "p[f.<aMxja"` and seven more). The Mutable side has no equivalent, which is why 3.2 adds one.
8. **The live collection is written only through `anki_sync_and_restore.py`** (`project-plans/completed/anki-card-cues-rework-11-03-26.md`, rule 7 and Phase 5.1). The only exception is the scheduling step, which goes through the committed tool from 3.1.
9. **Sync discipline** (memory `sync-anki-yourself`):
   - pull before any write;
   - close Anki;
   - back up;
   - sync up yourself afterwards (desktop route or the `prefs21.db` syncKey route; never hand the dialog to the user);
   - verify `col.ls >= col.mod` and `cards where usn=-1` = 0.
10. **Due rules**:
    - Unstudied words stay new except where the user asks (memory `unstudied-words-stay-new`). This ask names Degrees 0–1.
    - Only `type=0` cards are dated (memory `set-due-means-new-cards-only`).
    - Spreading goes through the tool, never a scratch script; if the tool can't express it, report and ask (memory `use-rebalance-tool-for-due-spreading`).
    - Any `--min` is hard (memory `rebalance-min-is-hard-no-exempt-tail`).
11. **TTS** (memories `tts-check-audio-before-upload`, `elevenlabs-key-lives-in-repo-dotenv`):
    - source the repo `.env` with `set -a; . ./.env; set +a` from the repo root, and never print the key;
    - gap-check every clip with silencedetect (n=-35dB, d=0.15), with the checker validated on a known-bad take first;
    - re-roll through `word_audio --replace`.
12. **Python code**:
    - every new non-test `.py` is paired with `tests/test_<base>.py` in the same change (smart-test hook);
    - black-compatible formatting;
    - minimal comments;
    - no scratch scripts for live writes.
13. **Parallel lanes run no git state commands**: no checkout, restore, stash, reset, clean, add, commit or push. Only read-only `git diff` and `git status`. A lane that thinks a file looks wrong reports it and does not revert it (memory `parallel-lanes-must-not-run-git-checkout`). Every dispatch carries this ban.
14. **Verification hygiene** (memory `false-clean-verification-pattern`): absolute paths; a positive control in the same invocation; capture output to a file rather than piping into `head`/`tail`; assert on content.
15. **Plans never carry time estimates.** No attribution trailers on any commit.

## Phase 1: Intake tooling and the skeleton

### 1.1: `noun_intake` module: candidates, forms, fragment validator, merge
- **File scope:**
  - `libs/python/anki-tools/anki_tools/noun_intake.py` (new);
  - `libs/python/anki-tools/tests/test_noun_intake.py` (new).
- **Pattern to follow:** `anki_tools/form_fill.py`, a pure module with tests.
  - Reuse its loaders and helpers rather than copying them: `extract_entries`, `load_openrussian`, `openrussian_value`, `generate_value`, `cross_check`, `house_stress`, `normalize_lemma`, `wiktionary_url`.
  - Parse output rows with `mutable_words_plan.parse_nouns`.
  - GUIDs come from `anki_identity.guid_for_row`.
- **Behaviour (the contract):**
  1. `load_frequency(path)` returns the `PoS == "s"` rows sorted by descending ipm. `top_nouns(rows, n)` takes the first n.
  2. `match_key(text)`: strip U+0301, fold ё→е, strip a trailing ` (…)` qualifier, lowercase. `missing(top, nouns_rows)` lists the top nouns with no `nouns.tsv` row under `match_key`.
  3. `classify(candidate, other_headwords)` flags each candidate with zero or more of:
     - `immutable-present`: in `source-word-list.md`;
     - `other-sheet-homonym`: a headword in verbs, adjectives, adverbs, pronouns or numerals;
     - `adjectival`: Wiktionary marks it as declining like an adjective, or it has an adjective ending;
     - `plural-only`;
     - `indeclinable`;
     - `no-wiktionary-noun`: no kaikki noun entry, so a likely mis-lemma, like стать.
  4. `skeleton_row(candidate, entries, or_index)` fills `Stress`, `Gender`, `Plural`, `Genitive Sg`, `Genitive Pl` and `Animate` from kaikki. Each value is cross-checked against OpenRussian with `cross_check`. A disagreement or missing value leaves the cell empty, and its reason goes in a `flags` column.
     - Gender uses the existing vocabulary `m`/`f`/`n`/`pl-only`/`pl form`.
     - Animate uses `Yes`/`No`.
     - A missing plural is `—`.
  5. `validate_fragment(path, sheet)` returns the violations. `sheet` ∈ {Nouns, Adjectives, Adverbs}; the header for Adjectives and Adverbs is that TSV's own header, with no `Degrees`. It is the contract every drafting lane must pass:
     - the header is exact: the `nouns.tsv` columns plus `Degrees`, and for skeleton/batch files only, the trailing `ipm` and `flags`;
     - `Status` = `New`;
     - `Examples` is empty;
     - `Category` is in the set of categories used by existing rows;
     - `Gender` and `Animate` are in the existing value sets;
     - `Degrees` ∈ {0,1,2,3};
     - `English` is non-empty, has no Cyrillic, and has no top-level separator other than ` / `;
     - `Stress` is in house format and folds back to `Russian`;
     - no empty form cell unless it is `—`;
     - `flags` is empty in a batch file, meaning every skeleton flag was resolved.
  6. `merge_rows(tsv_path, fragment_paths)` appends adjective or adverb fragment rows, with `#` continuing from the last rank and existing lines byte-identical. It raises on a duplicate GUID.
  7. `merge(nouns_path, batch_paths, existing_degree_paths)` returns the new `nouns.tsv` text:
     - existing rows keep every byte except that a `Degrees` cell is appended;
     - new rows are appended in descending-ipm order, with `#` continuing from the last existing rank;
     - `ipm` and `flags` are dropped;
     - it raises on a duplicate GUID, on an existing row without a Degrees value, or on a new row present in two batches.
- **Acceptance:** each function is covered by tests on small fixture files written under `tmp_path`. One of those tests uses a positive control: a seeded duplicate GUID that `merge` must reject.
- **Test oracle:** `new contract tests`.

### 1.2: Fetch the sources, generate the skeleton and the candidate report
- **File scope:**
  - `libs/python/anki-tools/anki_tools/data/russian-vocabulary/noun-intake/skeleton.tsv` and `noun-intake/candidates.md`. These are staging files, and 4.1 deletes them.
  - The downloads go in the run dir's `sources/` (gitignored): the kaikki Russian jsonl, the OpenRussian nouns/verbs/adjectives CSVs that `load_openrussian` expects, and a copy of `freqrnc2011.csv`.
- **Steps:**
  1. Download each source into its own empty directory, and read them with `python -I` (environment rule for untrusted data).
  2. Run the 1.1 functions through `uv run python -I -c` / `-m` from the package. No uncommitted logic.
  3. Apply D1–D4 as decided at the plan gate (see Risks, open questions, decision points).
- **Outputs:**
  - `skeleton.tsv`: one row per kept candidate, in descending ipm, with the forms filled and `flags` set.
  - `candidates.md`: the kept count; each exclusion class with its words; the `(noun)`-qualified words; and the flag histogram.
- **Acceptance:**
  - kept + excluded = 1,465, where excluded is exactly the 10 indeclinables already present plus привет (D1 as decided);
  - `candidates.md` lists the `adjectival` class, with each noun's adjective lemma and whether `adjectives.tsv` has it; 2.5 drafts from this list;
  - it also lists every same-spelling pair across all six TSVs and the Immutable list, which is the input to 4.2;
  - every kept row has a unique GUID against all six TSVs plus the Immutable list;
  - the flag histogram is reported, and no form value is invented to clear a flag.
- **Test oracle:** `equivalence check`. A recount from the csv with an independent one-liner matches `candidates.md`, and the positive control is that `правда (noun)` is counted as present.

## Phase 2: Row drafting

All four lanes share the same shape and differ only in their slice. The skeleton is split into four contiguous quarters by ipm order; quarter boundaries are written into `candidates.md` by 1.2. Each lane drafts two things.
- **Its quarter's new rows.** It writes `English`, `Category` and `Additional Info` in the existing style, and resolves every flag by checking en and ru Wiktionary. A resolved form cites its entry URL in the exit report.
  - `Additional Info` is used only for what existing rows put there: irregular declension, "declines like an adjective", fleeting vowels, and similar. Empty is normal (546 of 631 existing rows are empty).
- **`Degrees` for its quarter of the new rows, and for its slice of the existing 631 rows.** It uses the scale in Goal & scope and calibrates against the anchors:
  - телефон, министр, брат, нос, вода, стол, город and дом are existing rows;
  - автор, федерация and церковь are new rows.
  - The lane that owns an anchor must give it the user's value.

Each lane:
- runs `noun_intake.validate_fragment` on its batch until it returns no violations;
- never edits `nouns.tsv`, the skeleton, or another lane's file;
- runs no git state command (convention 13).

### 2.1: Batch A: new rows, quarter 1, and Degrees for existing rows 1–158
- **File scope:** `noun-intake/batch-a.tsv`, `noun-intake/existing-degrees-a.tsv` (`#`, `Russian`, `Degrees`).
- **Acceptance:**
  - `validate_fragment` is clean;
  - every row in quarter 1 is present exactly once;
  - existing ranks 1–158 each have one Degrees value;
  - anchors in this slice hold;
  - the Cyrillic scan of `English` returns 0, with a positive control on a seeded string.
- **Test oracle:** `equivalence check` (the 1.1 validator plus anchor assertions).

### 2.2: Batch B: new rows, quarter 2, and Degrees for existing rows 159–316
- **File scope:** `noun-intake/batch-b.tsv`, `noun-intake/existing-degrees-b.tsv`.
- **Acceptance / oracle:** as 2.1, for its slice.

### 2.3: Batch C: new rows, quarter 3, and Degrees for existing rows 317–474
- **File scope:** `noun-intake/batch-c.tsv`, `noun-intake/existing-degrees-c.tsv`.
- **Acceptance / oracle:** as 2.1, for its slice.

### 2.4: Batch D: new rows, quarter 4, and Degrees for existing rows 475–631
- **File scope:** `noun-intake/batch-d.tsv`, `noun-intake/existing-degrees-d.tsv`.
- **Acceptance / oracle:** as 2.1, for its slice.

### 2.5: Adjective and adverb rows for the nouns that are also adjectives
- **File scope:** `noun-intake/adjectives-new.tsv` and `noun-intake/adverbs-new.tsv`, plus `noun-intake/no-adverb.md` (adjectives with no real adverb, each with its reason).
- **Pattern to follow:**
  - existing `adjectives.tsv` rows, e.g. `новый`: Feminine, Neuter, Plural, Short Form, Comparative, Opposite, Stem Type;
  - existing `adverbs.tsv` rows, e.g. `по-новому`: `From Adjective`, `Formation`, `Comparative`;
  - forms come from the 1.1 loaders, cross-checked against OpenRussian and Wiktionary.
- **Scope rule:** one adjective row per `adjectival` noun whose masculine lemma is absent from `adjectives.tsv`. One adverb row per new adjective that has a real derived adverb. Only lemmas with an attested dictionary sense are used; no adverb is invented.
  - A row whose spelling equals a noun or other headword carries ` (adjective)` or ` (adverb)`.
  - Russian -о adverbs are glossed as predicatives ("it is X"), per memory `russian-o-adverbs-are-predicatives`.
- **Acceptance:**
  - `validate_fragment(…, "Adjectives")` and `validate_fragment(…, "Adverbs")` are clean;
  - every new adjective has an adverb row or a `no-adverb.md` entry;
  - the English columns contain no Cyrillic;
  - no lane-2–5 file is touched.
- **Test oracle:** `equivalence check` (the 1.1 validator).

## Phase 3: New-card scheduling tool

### 3.1: `anki-new-due`: dates new cards at a per-day rate
- **Why a tool is needed.** `anki-rebalance-due` cannot express this ask, verified in `anki_tools/rebalance_due.py`:
  - it plans only cards with `queue == 2 and type == 2` and skips new cards (lines ~139–151);
  - it selects by deck, not by a list of notes;
  - its `--min/--max` count every review card in the deck, including the existing ~4–5/day tail.
  
  Per memory `use-rebalance-tool-for-due-spreading`, this gap was reported at the plan gate, and the user chose D6 = A, a new committed tool.
- **File scope:**
  - `libs/python/anki-tools/anki_tools/new_due.py` (new) and `tests/test_new_due.py` (new);
  - a `bin` entry `anki-new-due` in `libs/python/anki-tools/package.json`;
  - `tests/test_entry_point_bins.py` if it pins the bin list.
- **Pattern to follow:** `anki_tools/phrase_due_cli.py` and `anki_tools/counterpart_due_cli.py`, committed CLIs that already date new cards with `col.sched.set_due_date`. Also follow `rebalance_due.py` for `--collection`, the backup, `--dry-run`, the confirmation prompt, `--yes`, and `get_anki_collection_path`.
- **Behaviour:**
  - **Input.** An ordered file of note GUIDs, and either `--first-due YYYY-MM-DD` or `--start-offset N`. `--per-day` counts cards. `--same-day-siblings` (default on) keeps a note's cards together.
  - **Refusals.** It refuses, writing nothing, if:
    - any target card is not `type=0 queue=0`, or is suspended;
    - `per-day` is not divisible by cards-per-note;
    - a GUID is not found.
  - **Plan.** Slot k (0-based) goes to day `first + k // notes_per_day`.
  - **Dry-run.** Prints a per-day histogram that includes the deck's other due cards on those days, so the user sees the combined load.
  - **Real run.** Takes a backup, then calls `set_due_date([cids], str(offset))` once per day group. It then asserts that every card landed on its planned day and that no other card changed (`type`, `queue`, `due`, `ivl` snapshot of the deck).
- **Acceptance:** contract tests on a scratch collection built in `tmp_path` cover:
  - order;
  - per-day grouping;
  - sibling co-location;
  - each refusal, with a positive control that a review card in the list is refused;
  - no change to untouched cards;
  - the date-to-offset conversion relative to `col.sched.today`.
- **Test oracle:** `new contract tests`.

### 3.2: GUID pins for Mutable rows whose headword gains a qualifier
- **File scope:**
  - `libs/python/anki-tools/anki_tools/mutable_words_plan.py`: a `GUID_PINS: dict[tuple[str, str], str]` keyed by `(sheet, stored headword)`, consulted first in every row class's `guid` property (`NounRow`, `VerbRow`, `AdjectiveRow`, `AdverbRow`, `PronounRow`, `NumeralRow`). The dict starts empty here and 4.2 fills it.
  - `libs/python/anki-tools/tests/test_mutable_words_plan.py`.
- **Pattern to follow:** `immutable_words_plan.GUID_PINS` and `WordRow.guid` (`GUID_PINS.get((self.pos, self.russian)) or guid_for_row(...)`).
- **Acceptance:** contract tests cover the following:
  - a pinned `(sheet, headword)` returns the pinned GUID;
  - an unpinned row still returns `guid_for_row(base_words[0], sheet)`;
  - a pin keyed to another sheet does not apply;
  - with an empty dict, every existing row's GUID is unchanged. The positive control computes all GUIDs before and after.
- **Test oracle:** `new contract tests`.

## Phase 4: Integration

### 4.1: Add the Degrees column; merge the noun, adjective and adverb fragments
- **File scope:**
  - `anki_tools/data/russian-vocabulary/nouns.tsv`;
  - `adjectives.tsv` and `adverbs.tsv` (rows appended through `merge_rows`);
  - `tests/test_vocabulary_data.py` line counts for those two files;
  - deleting `anki_tools/data/russian-vocabulary/noun-intake/` entirely;
  - `tests/test_vocabulary_data.py`: `EXPECTED_HEADERS["nouns.tsv"]`, `EXPECTED_LINE_COUNTS`, and the `("nouns.tsv","Plural")` dash count;
  - a new test there asserting `Degrees` ∈ {0,1,2,3} on every row and the 11 anchors.
- **Column placement:** append `Degrees` **after `Status`**. This mirrors `adverbs.tsv`, whose `Case` column trails `Status`. Existing lines then gain only `\t<degree>` and nothing shifts.
- **Why no build change is needed.** Every reader of `nouns.tsv` addresses cells by header name, so an extra column is ignored:
  - `mutable_words_plan.parse_nouns` uses `csv.DictReader` with named keys;
  - `form_census`, `source_drift` and `collisions` go through `parse_nouns`;
  - `tests/test_examples_field.py` rewrites by `header.index`.
  
  `FIELD_NAMES["Nouns"]` (in `mutable_words_plan.py`) and the note type stay unchanged.
- **Acceptance:**
  - the file equals `noun_intake.merge(...)`;
  - a byte-diff of the 631 existing lines, with the trailing Degrees cell stripped, against `git show HEAD:` is empty;
  - `parse_nouns` returns 631 + kept rows, and `parse_adjectives` / `parse_adverbs` return the old count plus the 2.5 rows;
  - the existing adjective and adverb lines are byte-identical;
  - `source_drift` shows identical built `fields` for the existing notes;
  - the staging dir is gone.
- **Test oracle:** `existing suite` plus `new contract tests` (the Degrees test).

### 4.2: Qualify existing same-spelling rows, pin their GUIDs, rekey their cue rows
- **File scope:**
  - the Russian headword cell of the named existing rows in `adjectives.tsv`, `adverbs.tsv`, `verbs.tsv` and `numerals.tsv`;
  - the `пора` row in `tests/data/source-word-list.md`;
  - `mutable_words_plan.GUID_PINS` and `immutable_words_plan.GUID_PINS`: each renamed row is pinned to its **pre-rename** GUID, computed from `HEAD`;
  - `distinction.ENGLISH_DISTINCTIONS` and `qualifier-classification.tsv` (`headword (keyed)`): rekey the entries of renamed rows, with the cue text unchanged;
  - an `adverbs.tsv` `From Adjective` cell that names a renamed adjective, but only if a test or the builder links by that text. Check `mutable_words_plan.parse_adverbs` and `tests/test_mutable_words_plan.py` first; otherwise leave it.
- **The rows:**
  - больной, русский, знакомый `(adjective)`;
  - зло, тепло `(adverb)`;
  - печь `(verb)`;
  - тысяча `(numeral)`;
  - пора `(adverb)`;
  - стать per D10;
  - any pair added by 1.2 / 2.5, including existing noun rows such as `рабочий`, which gains `(noun)` when 2.5 adds the adjective `рабочий (adjective)`.
- **Acceptance:**
  - for every renamed row, `row.guid` equals its `HEAD` GUID, asserted in a test listing each pin;
  - `test_shared_russian_spellings_carry_distinct_labels` passes;
  - a new test asserts that **every same-spelling pair touched by this run is labelled on both sides**, with no empty `Russian Distinction`. Its positive control is a seeded unlabelled pair that fails;
  - all other cells of these rows are byte-identical to `HEAD`;
  - audio filenames are unchanged (`audio_naming.strip_qualifier`).
- **Test oracle:** `new contract tests` plus `existing suite`.

### 4.3: Pinned counts, freeze baseline, GUID uniqueness, full suite
- **File scope:**
  - `tests/data/meaning-freeze-baseline.tsv`: append `guid`, `note type`, `Russian` and `Translation` for each new note, following commit `5caa13e`, which appended 142;
  - `tests/test_qualifier_classification.py`: the 1617 baseline count, and `NEW_VERB_HEADWORDS` only if the added-set assertion needs it;
  - `tests/test_collisions.py`: `test_load_notes_counts_and_order` 1623 and `631`;
  - `tests/test_form_census.py` (`"Nouns": 631`);
  - `tests/test_mutable_words_plan.py` (`len(nouns) == 631`);
  - `tests/test_mutable_words_e2e.py` (`"Nouns": 631` and `len(nouns) == 631`);
  - plus any other pin the suite surfaces.
- **Steps:**
  1. Run the full suite.
  2. For each failure, confirm it is a pure count or set pin caused by the new rows before updating it. List every updated pin, old → new, in the exit report.
  3. Investigate any non-count failure. Never paper over it.
- **Acceptance:**
  - the full suite and ruff are green;
  - there is a test asserting no two Nouns rows share a GUID;
  - a grep for `631` and `1623` under `tests/` (with a positive control run before the edit) shows no stale pin.
- **Test oracle:** `existing suite`.

### 4.4: Regenerate the similarity table and list the new collisions, both sides
- **File scope:** `anki_tools/data/russian-vocabulary/similarity-groups.tsv` (generated), plus a run-dir report `new-collisions.md`.
- **Steps:** run `uv run python -m anki_tools.collisions --write-similarity-table`. Then diff the table against `HEAD` and list:
  - (a) new groups;
  - (b) existing groups that gained a member;
  - (c) every word whose `told apart by` became `cue` but has no cue, split into new words and existing words;
  - (d) the Russian side: every spelling shared by two or more cards (the `_shown_spellings` logic in `tests/test_russian_lookalikes.py`), with each side's current label.
- **Acceptance:** the staleness test passes, and the report enumerates every (c) and (d) row.
- **Test oracle:** `existing suite`.

## Phase 5: Cues for new collisions, both sides

### 5.1: Draft English and Russian cues, show one approval table
- **File scope:** run-dir `cue-table.md` only.
- **Steps:** for every 4.4(c) and 4.4(d) word, look the word up in en and ru Wiktionary, then draft a cue under convention 6. Words that are not `cue` get no cue.
- **The table**, shown once and not per batch:
  - `word | group(s) | gloss | Russian-side label | English-side cue`;
  - Russian-side labels are the qualifiers from 4.2 and the new rows, shown so the user sees both sides together;
  - existing words that newly need a cue are a separate section;
  - any existing non-empty cue that no longer separates is **listed, not rewritten**.
- **Acceptance:**
  - every 4.4(c) and 4.4(d) row appears once;
  - the cue lint passes: no brackets, no example phrasing, no case names, no bare restatement of the gloss, and a part-of-speech name only where it is the separating fact;
  - the user approves.
- **Test oracle:** `equivalence check` plus human sign-off.

### 5.2: Write the approved cues, regenerate, byte-diff the rest
- **File scope:**
  - `anki_tools/distinction.py` (`ENGLISH_DISTINCTIONS`, keyed by stored headword including any qualifier);
  - `anki_tools/data/russian-vocabulary/qualifier-classification.tsv`, adding rows for newly cued notes as `5caa13e` did;
  - `similarity-groups.tsv` (regenerated);
  - the pins `test_artifact_sizes` (954) and the collision totals in `tests/test_collisions.py`.
- **Acceptance:**
  - written cues equal the approved table byte for byte;
  - every other `English Distinction` and `Translation` value equals `HEAD`, diffed per note and reported as an exact list;
  - `test_unclassified_notes_carry_no_cue` and `test_every_english_distinction_key_matches_a_headword` pass;
  - the full suite is green.
- **Test oracle:** `existing suite` plus `equivalence check`.

### 5.3: README cue rules: part-of-speech labels allowed for same-spelling words
- **File scope:** `anki_tools/data/russian-vocabulary/README.md` ("Similarity groups and cues" section).
- **Change:**
  - The rule "A cue never repeats the English or the Info, never names a part of speech or a case" now allows a part-of-speech label when it is what separates same-spelling words.
  - Add: "Same-spelling words are labelled on both cards with their part of speech in the headword qualifier (`печь (noun)` / `печь (verb)`), which fills `Russian Distinction`."
  - Add the `Degrees` column under Files/Editing: the scale and the anchors, noting that it is not a card field.
- **Acceptance:** `test_readme_states_tsvs_are_only_source` passes, and the text matches the user's words without widening them.
- **Test oracle:** `existing suite`.

## Phase 6: Offline build check

### 6.1: Dry-run counts, build against a collection copy, scratch import
- **File scope:** run dir only.
- **Steps:**
  1. `uv run anki-mutable-words --dry-run`: the Nouns count is 631 + kept, at 2 cards each (`TEMPLATE_COUNTS_BY_SHEET["Nouns"]`).
  2. Build `--out` into the run dir from a **copy** of the live collection (`--collection <copy>`).
  3. Import into a second scratch copy with the same `ImportAnkiPackageOptions` as `anki_sync_and_restore.rebuild`.
- **Acceptance:**
  - the new note count equals kept nouns + new adjectives + new adverbs, with 0 conflicting;
  - each renamed (pinned) note is **updated, not new**: same note id, a new `Russian Distinction`, every other field identical;
  - every other existing note has field-identical content;
  - every new card is `type=0` in `Languages::Russian::4. Mutable Words::a. Nouns` (`subdeck_name("Nouns")`);
  - the review state from `review_state` is unchanged;
  - the live file's mtime is untouched.
- **Test oracle:** `equivalence check`.

## Phase 7: Audio

### 7.1: Dry-run the request count, confirm, generate
- **File scope:** the Anki media dir and `~/Desktop/russian-audio` (`elevenlabs_tts.DEFAULT_OUTPUT_DIR`).
- **Request count:**
  - It is 2 per new headword (voices f1 and m2), minus clips already in the media dir. Homographs reuse audio through `strip_qualifier`: больной, русский, знакомый, зло, тепло, печь, тысяча, пора, привет.
  - **Upper bound ≈ 2 × (kept nouns + new adjectives + new adverbs − headwords that already have clips)**. The nouns account for about 2,900 requests (~1,450 kept), before any re-rolls; adjectives and adverbs add 2 per new headword.
  - Dry-run all three sheets: `--sheet Nouns`, `--sheet Adjectives`, `--sheet Adverbs`. The exact figure comes from `uv run anki-mutable-words-audio --sheet Nouns --dry-run`.
  - Any difference from 2 × (kept − homographs with existing clips) is explained before the run.
- **Steps:**
  1. Report the dry-run count.
  2. Get the user's yes (`CONFIRM_ABOVE_REQUESTS = 1`).
  3. Source `.env` and confirm the key is present without printing it.
  4. Run the tool. It is resumable and skips existing files.
- **Acceptance:** every new headword has `<slug>_f1.mp3` and `<slug>_m2.mp3`, with names from `mutable_words_plan.audio_names`.
- **Test oracle:** `equivalence check`.

### 7.2: Gap-check every new clip with a validated checker, re-roll the broken ones
- **File scope:** the media dir; the run dir (the checker and its output).
- **Steps:**
  1. Validate the checker on a known-bad take first. The rule: silencedetect n=-35dB d=0.15; a silence starting after 0.03 s with more than 0.12 s of audio after it counts as broken.
  2. Check every new clip.
  3. Re-roll each broken clip with `uv run anki-word-audio --mode single --replace --no-sync -- <word>` until none are broken.
  4. Have the user listen to the homograph clips that already existed (больной, русский, …) to confirm they suit the noun reading. Stress can differ, e.g. печь noun vs verb, which share a stress.
- **Acceptance:**
  - `broken 0`, with the control reported broken;
  - the re-roll count is reported.
- **Test oracle:** `equivalence check`.

## Phase 8: Live apply

All of Phase 8 runs in the main session, in the foreground, never in a builder.

### 8.1: Pull, close Anki, back up, source-drift check
- **File scope:** the live profile (read and sync only); `~/anki-backups/`.
- **Steps:**
  1. Confirm the phone has synced.
  2. Pull: `setsid nohup anki >/dev/null 2>&1 </dev/null & disown`, let it sync down, then `pkill -x anki`, and confirm that `pgrep -x anki` is empty.
  3. Back up `collection.anki2` and `-wal`, and check that `PRAGMA integrity_check` returns `ok`.
  4. Run `uv run anki-source-drift`. Any live edit to an existing noun is adopted into the TSV for those rows only, and shown first.
- **Acceptance:** integrity is ok; drift is 0, or reconciled with the user's approval.
- **Test oracle:** `equivalence check`.

### 8.2: Build both packages and run `--stage rebuild`
- **File scope:**
  - `~/Desktop/anki-rebuild/mutable-words.apkg` and `immutable-words.apkg` (`anki_sync_and_restore.PACKAGES`);
  - the live collection, through the script only.
- **Steps:**
  1. `anki-mutable-words --out … --audio-dir ~/Desktop/russian-audio --force`.
  2. `anki-immutable-words --source tests/data/source-word-list.md --audio-dir … --out …`, following plan `anki-card-cues-rework-11-03-26`, 5.1.
  3. `python anki_sync_and_restore.py --stage rebuild`.
- **Acceptance** (from the script output, saved):
  - mutable: `new` = kept nouns + new adjectives + new adverbs, `conflicting` = 0;
  - immutable: 0 new; `пора (adverb)` is updated under its pinned GUID;
  - no duplicate notes by headword with the qualifier stripped, beyond the intended homonyms;
  - `review_state` is unchanged apart from the phrase-word cards (D7);
  - the new noun cards are `type=0`;
  - `col.media.check()` reports 0 missing for the new clips.
- **Test oracle:** `equivalence check`.

### 8.3: Sync up and verify
- **File scope:** the live profile; AnkiWeb.
- **Steps:**
  1. Desktop route: launch Anki detached so it syncs, then close it. If a full-sync dialog appears, use the `prefs21.db` syncKey route instead (memory `sync-anki-yourself`). None is expected, because no schema changes.
  2. Run `anki_sync.sync(names)` for the new media.
- **Acceptance:**
  - on a scratch copy, `col.ls >= col.mod`;
  - `usn=-1` cards = 0;
  - the media checksums are present and not dirty.
- **Test oracle:** `equivalence check`.

## Phase 9: Schedule the Degrees 0–1 nouns

### 9.1: Build the ordered list, dry-run, show the histogram
- **File scope:** run dir (`degree01-guids.txt`, dry-run output).
- **Steps:**
  1. Build the list: new rows only, `Degrees` ∈ {0,1}, ordered by ipm descending, as GUIDs. Show the word list once (D8).
  2. Run `uv run anki-due-stats` over `Languages::Russian` to re-confirm that the queue still clears by 2026-12-06. If it has shifted, report it and ask.
  3. Run `anki-new-due --dry-run --first-due 2026-12-07 --per-day 10`.
- **Acceptance:**
  - the histogram shows 10 of these cards a day, both cards of a note on the same day, from 2026-12-07, ending on day ⌈count/5⌉, with the combined per-day load shown;
  - the user approves.
- **Test oracle:** `equivalence check`.

### 9.2: Apply, counterpart check, sync
- **File scope:** the live collection (through `anki-new-due`); AnkiWeb.
- **Steps:**
  1. Pull, close Anki, and back up (as in 8.1).
  2. Run the identical command without `--dry-run`.
  3. Run `anki-counterpart-due "Languages::Russian"` and expect 0.
  4. Sync as in 8.3.
- **Acceptance:**
  - the tool's own assertions pass;
  - the Degrees 2–3 new cards and the 535 existing nouns are unchanged (`type`/`queue`/`due` snapshot diff);
  - the sync is verified.
- **Test oracle:** `equivalence check`.

## Phase 10: Record

### 10.1: README, docs page and changelog
- **File scope:**
  - `docs/libs/python/anki-tools/` (the existing `mutable-words.md`, plus a page for `anki-new-due`);
  - the changelog.
  
  The documenter carries this out through `document-local`.
- **Acceptance:** `test_readme_states_tsvs_are_only_source` still passes, and docs follow `doc-format`.
- **Test oracle:** `existing suite`.

## Risks, open questions, decision points

**Resolved at the plan gate** (user, 11-26-26, verbatim entry in the Ask of record; detail relayed by the coordinator):
- **D1, decided.**
  - Skip the 10 indeclinables already in Immutable, and привет.
  - Add every other same-spelling word as a `(noun)` row: пора, тысяча, больной, русский, знакомый, зло, тепло, печь, стать.
  - Qualify the existing other-deck row where it lacks a qualifier (4.2), with its GUID pinned (3.2).
- **D2, decided.** Nouns that are also adjectives go in both decks, adjectives get their adverbs, and same-spelling pairs are labelled on both sides (2.5, 4.2).
- **D3, decided.** New indeclinables not already present go in `nouns.tsv`, with `Plural` `—` and an Additional Info note.
- **D4, decided.** No back-fill past the cutoff.
- **D5, decided.** 10 cards = 5 nouns a day, both cards on the same day, in frequency order, from 2026-12-07.
- **D6, decided: A.** A new committed `anki-new-due` tool (3.1).
- **D7, decided: accepted.** The phrase-word due count from `--stage rebuild` is reported at 8.2.
- **D8, decided.** No per-batch Degrees review; the Degrees 0–1 list is shown once at 9.1.
- **D9, decided.** One cue table, both sides, shown before writing (5.1).

**Still open:**
- **D10: Labelling стать on the verb side.** стать is the **Perfective** of `становиться / стать` (`verbs.tsv` #193). A verb note's `Russian Distinction` comes from `qualifier_of(self.imperfective)` only (`mutable_words_plan.py`, the `VerbRow.fields` line `distinction.qualifier_of(self.imperfective)`). So no cell edit can label the perfective alone.
  - **(A, recommended)** Qualify the imperfective as `становиться (verb)`. The whole verb note is then labelled `verb`, and the `(noun)` row tells стать apart. The imperfective's GUID is pinned in 4.2.
  - (B) Code change: read a qualifier from either aspect cell. This touches `VerbRow` and is outside the asked scope.
  - (C) Leave the verb side unlabelled. Today's test allows one unlabelled side, but the user asked for both sides.
- **D11: Existing same-spelling pairs this run does not touch.** 4.4(d) will list spellings already shared before this run where one side is unlabelled.
  - **Recommended:** report them, but leave them unchanged unless the user widens the ask. "same with words that have the same spelling as other words" may be meant to include them.
  - Alternative: label all of them in 4.2.
- **Risks:**
  - **Glosses at scale.** The drafting quality of ~1,450 glosses is the main risk. The validator enforces form, not meaning. 4.4 surfaces gloss clashes through the similarity table, and the review gate can sample rows.
  - **Inconsistent Degrees across four lanes.** Mitigated by the shared anchors. 4.1 can also print the per-lane distribution of Degrees so outliers are visible.
  - **Duplicate GUIDs.** A homonym added without a qualifier would duplicate a GUID; the `merge` raise and the 4.3 test catch it.
  - **Re-GUIDed existing notes.** A qualifier added to an existing headword without a pin would import as a duplicate note and orphan the studied note's history. 3.2, 4.2 and the 6.1/8.2 checks for "updated, not new" guard this.
  - **ElevenLabs quota.** About 2,900 requests may exceed the account's character or credit allowance. 7.1 checks the plan's remaining quota before it runs; the tool is resumable.
  - **The smart-lint hook reformats unrelated files** (memory `smart-lint-hook-fires-repo-wide`). Lanes restore only their own collateral and report anything else.
  - **Re-imports after this run.** `--stage rebuild` re-imports with `update_notes=ALWAYS`. Any live edit not adopted at 8.1 is overwritten, and 8.1's drift step guards that.
- **Unverified assumptions:**
  - The exact kept count and the flag histogram are not known until 1.2.
  - The noun share of Degrees 0–1, and so the length of the schedule, is not known until Phase 2.
  - That the kaikki jsonl and OpenRussian CSV URLs and their formats still match `form_fill`'s loaders is checked at 1.2.
  - That no new indeclinables exist is unverified.
  - The number of new adjective and adverb rows, and the full list of same-spelling pairs, are not known until 1.2.

## Skill mapping
- Planning: `planner` (this file), then `review-plan`.
- Phases 1–3: `builder` lanes 1–6, using `coder` and `contract-tester` for 1.1, 3.1 and 3.2. Lanes 2–6 are content work that runs against the 1.1 validator, with `init-workspace` per worktree.
- Phases 4–5: the main session or a single serial `builder`, then `review-code`.
- Phases 6–9: the main session, foreground (live data, confirmation-gated).
- Phase 10: `documenter` → `document-local`.
- Landing: local squash-merge into `main` per the repo `CLAUDE.md`. No PR, and `push-pr`/`review-pr` are not used for publishing.
